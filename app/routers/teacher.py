from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User, RoleEnum
from ..crud.discipline import get_teacher_disciplines
from ..schemas.discipline import TeacherDisciplineResponse, TeacherProfileResponse, SchoolInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teacher", tags=["teacher"])


def ensure_teacher(user: User):
    """Проверка что пользователь - учитель"""
    if user.role != RoleEnum.teacher:
        logger.warning(f"Access denied for user {user.id} with role {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуется роль TEACHER"
        )


@router.get("/disciplines", response_model=dict)
def get_my_disciplines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить список дисциплин, закрепленных за текущим учителем

    Returns:
        {
            "success": true,
            "data": [...]
        }
    """
    ensure_teacher(current_user)
    logger.info(f"Teacher {current_user.id} requesting their disciplines")

    try:
        # Получаем назначения с дисциплинами
        assignments = get_teacher_disciplines(db, current_user.id, active_only=True)

        # Преобразуем в response формат
        disciplines_data = []
        for assignment in assignments:
            # Получаем имя админа который назначил
            admin = db.query(User).filter(User.id == assignment.assigned_by).first()
            admin_name = admin.full_name if admin else "Неизвестно"

            discipline_response = TeacherDisciplineResponse.from_teacher_discipline(
                assignment,
                admin_name
            )
            disciplines_data.append(discipline_response.model_dump())

        logger.info(f"Teacher {current_user.id} has {len(disciplines_data)} disciplines")

        return {
            "success": True,
            "data": disciplines_data
        }

    except Exception as e:
        logger.error(f"Error fetching disciplines for teacher {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении дисциплин"
        )


@router.get("/profile", response_model=dict)
def get_teacher_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить профиль учителя (включая дисциплины)

    Returns:
        {
            "success": true,
            "data": {
                "id": 42,
                "name": "Анна Петровна Смирнова",
                "email": "a.smirnova@school125.edu",
                "school": {...},
                "assigned_disciplines": [...]
            }
        }
    """
    ensure_teacher(current_user)
    logger.info(f"Teacher {current_user.id} requesting their profile")

    try:
        # Получаем дисциплины
        assignments = get_teacher_disciplines(db, current_user.id, active_only=True)

        # Преобразуем в response формат
        disciplines_data = []
        for assignment in assignments:
            admin = db.query(User).filter(User.id == assignment.assigned_by).first()
            admin_name = admin.full_name if admin else "Неизвестно"

            discipline_response = TeacherDisciplineResponse.from_teacher_discipline(
                assignment,
                admin_name
            )
            disciplines_data.append(discipline_response)

        # Формируем профиль
        school_info = None
        if current_user.school:
            school_info = SchoolInfo(
                id=current_user.school.id,
                name=current_user.school.name
            )

        profile = TeacherProfileResponse(
            id=current_user.id,
            name=current_user.full_name,
            email=current_user.email,
            school=school_info,
            assigned_disciplines=disciplines_data,
            created_at=None  # Можно добавить created_at в модель User если нужно
        )

        logger.info(f"Successfully fetched profile for teacher {current_user.id}")

        return {
            "success": True,
            "data": profile.model_dump()
        }

    except Exception as e:
        logger.error(f"Error fetching profile for teacher {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении профиля"
        )
