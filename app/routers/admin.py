from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from typing import List, Optional

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User, RoleEnum
from ..models.school import School
from ..models.discipline import Discipline
from ..models.teacher_discipline import TeacherDiscipline
from ..models.parent_child import ParentChild
from ..models.student_stats import StudentStats
from ..models.student import Student
from ..auth.hashing import get_password_hash
from ..crud.discipline import (
    create_discipline,
    get_school_disciplines,
    get_discipline_by_id,
    assign_discipline_to_teacher,
    get_teacher_disciplines,
    remove_discipline_from_teacher,
    get_discipline_teachers,
)
from ..schemas.discipline import (
    DisciplineCreate,
    DisciplineResponse,
    DisciplineAssign,
    AssignmentResponse,
    TeacherDisciplineResponse,
    DisciplineWithTeachers,
    TeacherInfo,
    AssignedByInfo,
    VALID_SUBJECTS,
    SUBJECT_CODES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ========== Helper Functions ==========

def ensure_school_admin(user: User):
    """Проверка что пользователь - администратор школы"""
    if user.role != RoleEnum.school_admin:
        logger.warning(f"Access denied for user {user.id} with role {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуется роль SCHOOL_ADMIN"
        )


def ensure_same_school(admin: User, user: User):
    """Проверка что пользователь и админ из одной школы"""
    if admin.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор не привязан к школе"
        )

    if user.school_id != admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете управлять только пользователями своей школы"
        )


# ========== Disciplines Management ==========

@router.get("/disciplines", response_model=dict)
def get_all_disciplines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить все дисциплины школы администратора

    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 15,
                    "subject": "Физика",
                    "grade": 7,
                    "displayName": "Физика - 7 класс",
                    "assigned_teachers": [...],
                    "created_at": "..."
                }
            ]
        }
    """
    ensure_school_admin(current_user)

    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор не привязан к школе"
        )

    logger.info(f"Admin {current_user.id} requesting all disciplines for school {current_user.school_id}")

    try:
        disciplines = get_school_disciplines(db, current_user.school_id)

        # Формируем response с учителями
        data = []
        for discipline in disciplines:
            # Получаем учителей назначенных на эту дисциплину
            assignments = get_discipline_teachers(db, discipline.id, active_only=True)

            teachers_info = []
            for assignment in assignments:
                teacher_info = TeacherInfo(
                    teacher_id=assignment.teacher.id,
                    teacher_name=assignment.teacher.full_name,
                    assigned_at=assignment.assigned_at
                )
                teachers_info.append(teacher_info)

            discipline_data = DisciplineWithTeachers(
                id=discipline.id,
                subject=discipline.subject,
                grade=discipline.grade,
                displayName=f"{discipline.subject} - {discipline.grade} класс",
                assigned_teachers=teachers_info,
                created_at=discipline.created_at
            )
            data.append(discipline_data.model_dump())

        logger.info(f"Found {len(data)} disciplines for school {current_user.school_id}")

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        logger.error(f"Error fetching disciplines for school {current_user.school_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении дисциплин"
        )


@router.post("/disciplines", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_new_discipline(
    discipline_data: DisciplineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создать новую дисциплину в школе

    Request:
        {
            "subject": "Физика",
            "grade": 9
        }

    Returns:
        {
            "success": true,
            "message": "Дисциплина успешно создана",
            "data": {...}
        }
    """
    ensure_school_admin(current_user)

    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор не привязан к школе"
        )

    logger.info(f"Admin {current_user.id} creating discipline {discipline_data.subject} {discipline_data.grade}")

    try:
        discipline = create_discipline(db, current_user.school_id, discipline_data)

        discipline_response = DisciplineResponse.from_orm_with_display_name(discipline)

        logger.info(f"Successfully created discipline {discipline.id}")

        return {
            "success": True,
            "message": "Дисциплина успешно создана",
            "data": discipline_response.model_dump()
        }

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Такая дисциплина уже существует в вашей школе"
        )
    except Exception as e:
        logger.error(f"Error creating discipline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании дисциплины"
        )


@router.get("/available-subjects", response_model=dict)
def get_available_subjects(
    current_user: User = Depends(get_current_user),
):
    """
    Получить список доступных предметов для создания дисциплин

    Returns:
        {
            "success": true,
            "data": {
                "subjects": ["Математика", "Физика", ...],
                "subject_codes": {"Математика": "math", ...}
            }
        }
    """
    ensure_school_admin(current_user)

    logger.info(f"Admin {current_user.id} requesting available subjects")

    return {
        "success": True,
        "data": {
            "subjects": VALID_SUBJECTS,
            "subject_codes": SUBJECT_CODES
        }
    }


@router.get("/teachers", response_model=dict)
def get_school_teachers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить список всех учителей школы

    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 42,
                    "name": "Анна Петровна Смирнова",
                    "email": "a.smirnova@school125.edu",
                    "disciplines_count": 3
                }
            ]
        }
    """
    ensure_school_admin(current_user)

    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор не привязан к школе"
        )

    logger.info(f"Admin {current_user.id} requesting all teachers for school {current_user.school_id}")

    try:
        # DEBUG: Проверяем всех учителей в системе
        all_teachers = db.query(User).filter(User.role == RoleEnum.teacher).all()
        logger.info(f"DEBUG: Total teachers in system: {len(all_teachers)}")
        for t in all_teachers:
            logger.info(f"DEBUG: Teacher ID={t.id}, name={t.full_name}, school_id={t.school_id}")

        # Получаем всех учителей школы
        teachers = (
            db.query(User)
            .filter(User.school_id == current_user.school_id)
            .filter(User.role == RoleEnum.teacher)
            .order_by(User.full_name)
            .all()
        )

        logger.info(f"DEBUG: Teachers with school_id={current_user.school_id}: {len(teachers)}")

        # Формируем response с количеством дисциплин
        data = []
        for teacher in teachers:
            # Получаем количество активных дисциплин
            disciplines = get_teacher_disciplines(db, teacher.id, active_only=True)

            teacher_data = {
                "id": teacher.id,
                "name": teacher.full_name,
                "email": teacher.email,
                "disciplines_count": len(disciplines)
            }
            data.append(teacher_data)

        logger.info(f"Found {len(data)} teachers for school {current_user.school_id}")

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        logger.error(f"Error fetching teachers for school {current_user.school_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка учителей"
        )


@router.get("/debug/all-teachers", response_model=dict)
def debug_all_teachers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    DEBUG эндпоинт: Получить всех учителей в системе (для отладки)

    Показывает всех учителей независимо от школы
    """
    ensure_school_admin(current_user)

    logger.info(f"Admin {current_user.id} requesting DEBUG all teachers")

    try:
        # Получаем ВСЕХ учителей в системе
        all_teachers = db.query(User).filter(User.role == RoleEnum.teacher).all()

        data = []
        for teacher in all_teachers:
            disciplines = get_teacher_disciplines(db, teacher.id, active_only=True)

            teacher_data = {
                "id": teacher.id,
                "name": teacher.full_name,
                "email": teacher.email,
                "school_id": teacher.school_id,
                "school_name": teacher.school.name if teacher.school else "НЕ ПРИВЯЗАН К ШКОЛЕ",
                "disciplines_count": len(disciplines),
                "is_in_my_school": teacher.school_id == current_user.school_id
            }
            data.append(teacher_data)

        return {
            "success": True,
            "data": {
                "total_teachers": len(data),
                "admin_school_id": current_user.school_id,
                "teachers": data
            }
        }

    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка в debug эндпоинте"
        )


@router.post("/teacher/{teacher_id}/attach-to-school", response_model=dict)
def attach_teacher_to_school(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Привязать учителя к школе администратора

    Используется для индивидуальных учителей (school_id = NULL)
    чтобы они появились в списке учителей школы

    Returns:
        {
            "success": true,
            "message": "Учитель успешно привязан к школе",
            "data": {
                "teacher_id": 42,
                "teacher_name": "Иван Петров",
                "school_id": 1,
                "school_name": "Школа №125"
            }
        }
    """
    ensure_school_admin(current_user)

    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор не привязан к школе"
        )

    logger.info(f"Admin {current_user.id} attaching teacher {teacher_id} to school {current_user.school_id}")

    # Проверяем что учитель существует
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Учитель не найден"
        )

    # Проверяем что это учитель
    if teacher.role != RoleEnum.teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не является учителем"
        )

    # Проверяем что учитель еще не привязан к другой школе
    if teacher.school_id is not None and teacher.school_id != current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Учитель уже привязан к другой школе (ID: {teacher.school_id})"
        )

    # Если уже привязан к этой школе
    if teacher.school_id == current_user.school_id:
        return {
            "success": True,
            "message": "Учитель уже привязан к вашей школе",
            "data": {
                "teacher_id": teacher.id,
                "teacher_name": teacher.full_name,
                "school_id": current_user.school_id,
                "school_name": current_user.school.name if current_user.school else None
            }
        }

    try:
        # Привязываем к школе
        teacher.school_id = current_user.school_id
        db.commit()
        db.refresh(teacher)

        logger.info(f"Successfully attached teacher {teacher_id} to school {current_user.school_id}")

        return {
            "success": True,
            "message": "Учитель успешно привязан к школе",
            "data": {
                "teacher_id": teacher.id,
                "teacher_name": teacher.full_name,
                "school_id": current_user.school_id,
                "school_name": current_user.school.name if current_user.school else None
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error attaching teacher to school: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при привязке учителя к школе"
        )


# ========== Teacher Discipline Assignment ==========

@router.post("/teacher/{teacher_id}/assign-discipline", response_model=dict)
def assign_discipline(
    teacher_id: int,
    assignment_data: DisciplineAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Назначить дисциплину учителю

    Request:
        {
            "discipline_id": 15
        }

    Returns:
        {
            "success": true,
            "message": "Дисциплина успешно назначена учителю",
            "data": {...}
        }
    """
    ensure_school_admin(current_user)

    logger.info(f"Admin {current_user.id} assigning discipline {assignment_data.discipline_id} to teacher {teacher_id}")

    # Проверяем что учитель существует
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Учитель не найден"
        )

    # Проверяем что это учитель
    if teacher.role != RoleEnum.teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не является учителем"
        )

    # Проверяем что учитель из той же школы
    ensure_same_school(current_user, teacher)

    # Проверяем что дисциплина существует
    discipline = get_discipline_by_id(db, assignment_data.discipline_id)
    if not discipline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Дисциплина не найдена"
        )

    # Проверяем что дисциплина из той же школы
    if discipline.school_id != current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете назначать только дисциплины своей школы"
        )

    # Назначаем дисциплину
    try:
        assignment = assign_discipline_to_teacher(
            db,
            teacher_id,
            assignment_data.discipline_id,
            current_user.id
        )

        # Формируем response
        discipline_response = DisciplineResponse.from_orm_with_display_name(discipline)

        admin_info = AssignedByInfo(
            id=current_user.id,
            name=current_user.full_name
        )

        response_data = AssignmentResponse(
            teacher_id=teacher.id,
            teacher_name=teacher.full_name,
            discipline=discipline_response,
            assigned_by=admin_info,
            assigned_at=assignment.assigned_at
        )

        logger.info(f"Successfully assigned discipline {assignment_data.discipline_id} to teacher {teacher_id}")

        return {
            "success": True,
            "message": "Дисциплина успешно назначена учителю",
            "data": response_data.model_dump()
        }

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Эта дисциплина уже назначена данному учителю"
        )
    except Exception as e:
        logger.error(f"Error assigning discipline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при назначении дисциплины"
        )


@router.delete("/teacher/{teacher_id}/remove-discipline/{discipline_id}", response_model=dict)
def remove_discipline(
    teacher_id: int,
    discipline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Убрать дисциплину у учителя

    Returns:
        {
            "success": true,
            "message": "Дисциплина успешно удалена у учителя",
            "data": {
                "teacher_id": 42,
                "discipline_id": 15,
                "removed_at": "..."
            }
        }
    """
    ensure_school_admin(current_user)

    logger.info(f"Admin {current_user.id} removing discipline {discipline_id} from teacher {teacher_id}")

    # Проверяем что учитель существует
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Учитель не найден"
        )

    # Проверяем что учитель из той же школы
    ensure_same_school(current_user, teacher)

    # Проверяем что дисциплина существует
    discipline = get_discipline_by_id(db, discipline_id)
    if not discipline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Дисциплина не найдена"
        )

    # Проверяем что дисциплина из той же школы
    if discipline.school_id != current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете управлять только дисциплинами своей школы"
        )

    # Удаляем назначение
    try:
        from datetime import datetime

        removed = remove_discipline_from_teacher(db, teacher_id, discipline_id, soft_delete=True)

        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Данная дисциплина не назначена этому учителю"
            )

        logger.info(f"Successfully removed discipline {discipline_id} from teacher {teacher_id}")

        return {
            "success": True,
            "message": "Дисциплина успешно удалена у учителя",
            "data": {
                "teacher_id": teacher_id,
                "discipline_id": discipline_id,
                "removed_at": datetime.utcnow().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing discipline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении дисциплины"
        )


@router.get("/teachers/{teacher_id}/disciplines", response_model=dict)
def get_teacher_disciplines_admin(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить список дисциплин конкретного учителя (для админа)

    Returns:
        {
            "success": true,
            "data": {
                "teacher": {
                    "id": 42,
                    "name": "Анна Петровна Смирнова",
                    "email": "a.smirnova@school125.edu"
                },
                "disciplines": [...]
            }
        }
    """
    ensure_school_admin(current_user)

    logger.info(f"Admin {current_user.id} requesting disciplines for teacher {teacher_id}")

    # Проверяем что учитель существует
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Учитель не найден"
        )

    # Проверяем что учитель из той же школы
    ensure_same_school(current_user, teacher)

    try:
        # Получаем дисциплины учителя
        assignments = get_teacher_disciplines(db, teacher_id, active_only=True)

        # Формируем список дисциплин
        disciplines_data = []
        for assignment in assignments:
            admin = db.query(User).filter(User.id == assignment.assigned_by).first()
            admin_name = admin.full_name if admin else "Неизвестно"

            discipline_response = TeacherDisciplineResponse.from_teacher_discipline(
                assignment,
                admin_name
            )
            disciplines_data.append(discipline_response.model_dump())

        logger.info(f"Teacher {teacher_id} has {len(disciplines_data)} disciplines")

        return {
            "success": True,
            "data": {
                "teacher": {
                    "id": teacher.id,
                    "name": teacher.full_name,
                    "email": teacher.email
                },
                "disciplines": disciplines_data
            }
        }

    except Exception as e:
        logger.error(f"Error fetching teacher disciplines: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении дисциплин учителя"
        )


# ========== Parents Management ==========

@router.post("/parents/create")
def create_parent(
    email: str,
    password: str,
    full_name: str,
    children_ids: List[int],
    relationship: Optional[str] = "parent",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создать аккаунт родителя и привязать детей

    Args:
        email: Email родителя
        password: Временный пароль
        full_name: ФИО родителя
        children_ids: Список ID детей (users с role=student)
        relationship: Тип отношения ('father', 'mother', 'guardian')

    Returns:
        {
            "id": 111,
            "email": "parent@example.com",
            "full_name": "Иванов Петр Сергеевич",
            "role": "parent",
            "children_count": 2,
            "message": "Родитель успешно создан и привязан к детям"
        }
    """
    ensure_school_admin(current_user)

    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор не привязан к школе"
        )

    logger.info(f"Admin {current_user.id} creating parent {email}")

    # Проверяем, что email уникален
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    try:
        # Создаем родителя
        parent = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=RoleEnum.parent,
            school_id=current_user.school_id,
            is_verified=True
        )
        db.add(parent)
        db.flush()  # Получаем ID родителя

        # Привязываем детей
        children_count = 0
        for child_id in children_ids:
            # Проверяем, что ребенок существует и является студентом
            child = db.query(User).filter(User.id == child_id).first()
            if not child:
                logger.warning(f"Child {child_id} not found, skipping")
                continue

            if child.role != RoleEnum.student:
                logger.warning(f"User {child_id} is not a student, skipping")
                continue

            # Проверяем, что ребенок из той же школы
            if child.school_id != current_user.school_id:
                logger.warning(f"Child {child_id} from different school, skipping")
                continue

            # Создаем связь
            link = ParentChild(
                parent_user_id=parent.id,
                student_user_id=child.id,
                relationship=relationship,
                school_id=current_user.school_id
            )
            db.add(link)
            children_count += 1

        db.commit()
        db.refresh(parent)

        logger.info(f"Parent {parent.id} created with {children_count} children")

        return {
            "id": parent.id,
            "email": parent.email,
            "full_name": parent.full_name,
            "role": parent.role.value,
            "children_count": children_count,
            "message": "Родитель успешно создан и привязан к детям"
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating parent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка при создании родителя"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating parent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании родителя"
        )


@router.post("/parents/link-child")
def link_child_to_parent(
    parent_user_id: int,
    student_user_id: int,
    relationship: Optional[str] = "parent",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Привязать ребенка к существующему родителю

    Args:
        parent_user_id: ID родителя
        student_user_id: ID студента
        relationship: Тип отношения ('father', 'mother', 'guardian')

    Returns:
        {
            "success": true,
            "message": "Ребенок успешно привязан к родителю"
        }
    """
    ensure_school_admin(current_user)

    logger.info(f"Admin {current_user.id} linking child {student_user_id} to parent {parent_user_id}")

    # Проверяем родителя
    parent = db.query(User).filter(User.id == parent_user_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Родитель не найден")

    if parent.role != RoleEnum.parent:
        raise HTTPException(status_code=400, detail="Пользователь не является родителем")

    ensure_same_school(current_user, parent)

    # Проверяем ребенка
    student = db.query(User).filter(User.id == student_user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    if student.role != RoleEnum.student:
        raise HTTPException(status_code=400, detail="Пользователь не является студентом")

    ensure_same_school(current_user, student)

    # Проверяем, что связь еще не существует
    existing_link = db.query(ParentChild).filter(
        ParentChild.parent_user_id == parent_user_id,
        ParentChild.student_user_id == student_user_id
    ).first()

    if existing_link:
        raise HTTPException(
            status_code=400,
            detail="Ребенок уже привязан к этому родителю"
        )

    try:
        # Создаем связь
        link = ParentChild(
            parent_user_id=parent_user_id,
            student_user_id=student_user_id,
            relationship=relationship,
            school_id=current_user.school_id
        )
        db.add(link)
        db.commit()

        logger.info(f"Child {student_user_id} linked to parent {parent_user_id}")

        return {
            "success": True,
            "message": "Ребенок успешно привязан к родителю"
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ошибка при привязке ребенка")
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking child: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при привязке ребенка")


@router.delete("/parents/unlink-child")
def unlink_child_from_parent(
    parent_user_id: int,
    student_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Отвязать ребенка от родителя

    Args:
        parent_user_id: ID родителя
        student_user_id: ID студента

    Returns:
        {
            "success": true,
            "message": "Ребенок отвязан от родителя"
        }
    """
    ensure_school_admin(current_user)

    logger.info(f"Admin {current_user.id} unlinking child {student_user_id} from parent {parent_user_id}")

    # Проверяем родителя и студента
    parent = db.query(User).filter(User.id == parent_user_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Родитель не найден")

    ensure_same_school(current_user, parent)

    student = db.query(User).filter(User.id == student_user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    ensure_same_school(current_user, student)

    # Ищем связь
    link = db.query(ParentChild).filter(
        ParentChild.parent_user_id == parent_user_id,
        ParentChild.student_user_id == student_user_id
    ).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Связь между родителем и ребенком не найдена"
        )

    try:
        db.delete(link)
        db.commit()

        logger.info(f"Child {student_user_id} unlinked from parent {parent_user_id}")

        return {
            "success": True,
            "message": "Ребенок отвязан от родителя"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking child: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при отвязке ребенка")


@router.get("/parents/{parent_id}")
def get_parent_info(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить информацию о родителе и его детях

    Returns:
        {
            "id": 111,
            "email": "parent@example.com",
            "full_name": "Иванов Петр Сергеевич",
            "role": "parent",
            "is_active": true,
            "children": [
                {
                    "id": 456,
                    "name": "Иванова Анна Петровна",
                    "grade": "8 класс",
                    "relationship": "father"
                }
            ]
        }
    """
    ensure_school_admin(current_user)

    logger.info(f"Admin {current_user.id} requesting info for parent {parent_id}")

    # Проверяем родителя
    parent = db.query(User).filter(User.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Родитель не найден")

    if parent.role != RoleEnum.parent:
        raise HTTPException(status_code=400, detail="Пользователь не является родителем")

    ensure_same_school(current_user, parent)

    # Получаем детей
    parent_links = db.query(ParentChild).filter(
        ParentChild.parent_user_id == parent_id
    ).all()

    children_data = []
    for link in parent_links:
        student = db.query(User).filter(User.id == link.student_user_id).first()
        if not student:
            continue

        # Получаем класс из таблицы students
        student_info = db.query(Student).filter(Student.email == student.email).first()

        children_data.append({
            "id": student.id,
            "name": student.full_name,
            "grade": student_info.grade if student_info else None,
            "relationship": link.relationship
        })

    return {
        "id": parent.id,
        "email": parent.email,
        "full_name": parent.full_name,
        "role": parent.role.value,
        "is_active": getattr(parent, 'is_active', True),
        "children": children_data
    }
