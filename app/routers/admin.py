from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User, RoleEnum
from ..models.school import School
from ..models.discipline import Discipline
from ..models.teacher_discipline import TeacherDiscipline
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
