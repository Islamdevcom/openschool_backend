from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import Optional, List

from app.database import get_db
from app.models.user import User, RoleEnum
from app.models.parent_child import ParentChild
from app.models.student_stats import StudentStats
from app.schemas.auth import LoginRequest
from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


def _authenticate_user(email: str, password: str, db: Session) -> User:
    """Общая функция аутентификации"""
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный email или пароль"
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный email или пароль"
        )

    return user


def _generate_token_response(user: User, children_data: Optional[List[dict]] = None) -> dict:
    """Общая функция генерации ответа с токеном"""
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    response = {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "email": user.email,
        "full_name": user.full_name,
        "school_id": user.school_id
    }

    # Для родителей добавляем информацию о детях
    if children_data is not None:
        response["children"] = children_data

    return response


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Вход для УЧИТЕЛЕЙ, СТУДЕНТОВ и РОДИТЕЛЕЙ

    Для администраторов используйте:
    - /auth/admin/login (школьные администраторы)
    - /auth/superadmin/login (суперадминистраторы)
    """
    logger.info(f"Login attempt for email: {request.email}")

    user = _authenticate_user(request.email, request.password, db)

    # Проверяем что это teacher, student или parent
    if user.role not in [RoleEnum.teacher, RoleEnum.student, RoleEnum.parent]:
        logger.warning(f"User {user.email} tried to login via /auth/login with role {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Используйте специальный вход для администраторов"
        )

    # Для родителей - проверяем привязанных детей
    if user.role == RoleEnum.parent:
        logger.info(f"Parent {user.email} logging in, checking children...")

        # Получаем связи с детьми
        parent_links = db.query(ParentChild).filter(
            ParentChild.parent_user_id == user.id
        ).all()

        if not parent_links:
            logger.warning(f"Parent {user.email} has no linked children")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет привязанных детей. Обратитесь к администратору школы."
            )

        # Получаем данные о детях
        children_data = []
        for link in parent_links:
            # Получаем студента
            student = db.query(User).filter(User.id == link.student_user_id).first()
            if not student:
                continue

            # Получаем статистику студента
            stats = db.query(StudentStats).filter(
                StudentStats.student_user_id == student.id
            ).first()

            # Получаем информацию о классе (grade)
            # Примечание: В текущей модели User нет поля grade
            # Можно получить из таблицы students, если она используется
            from app.models.student import Student
            student_info = db.query(Student).filter(Student.email == student.email).first()

            child_data = {
                "id": student.id,
                "name": student.full_name,
                "email": student.email,
                "grade": student_info.grade if student_info else None,
                "relationship": link.relationship,
                "avgGrade": float(stats.avg_grade) if stats and stats.avg_grade else 0.0,
                "attendance": float(stats.attendance) if stats and stats.attendance else 0.0,
                "warnings": stats.warnings if stats else 0,
                "behavior": float(stats.behavior) if stats and stats.behavior else 0.0
            }
            children_data.append(child_data)

        logger.info(f"Parent {user.email} logged in successfully with {len(children_data)} children")
        return _generate_token_response(user, children_data=children_data)

    logger.info(f"User {user.email} logged in successfully as {user.role}")
    return _generate_token_response(user)


@router.post("/admin/login")
def admin_login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Вход для АДМИНИСТРАТОРОВ ШКОЛЫ

    Только для пользователей с ролью school_admin
    """
    logger.info(f"Admin login attempt for email: {request.email}")

    user = _authenticate_user(request.email, request.password, db)

    # Проверяем что это school_admin
    if user.role != RoleEnum.school_admin:
        logger.warning(f"User {user.email} tried to login via /auth/admin/login with role {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуется роль администратора школы"
        )

    logger.info(f"School admin {user.email} logged in successfully")
    return _generate_token_response(user)


@router.post("/superadmin/login")
def superadmin_login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Вход для СУПЕРАДМИНИСТРАТОРОВ

    Только для пользователей с ролью superadmin
    """
    logger.info(f"Superadmin login attempt for email: {request.email}")

    user = _authenticate_user(request.email, request.password, db)

    # Проверяем что это superadmin
    if user.role != RoleEnum.superadmin:
        logger.warning(f"User {user.email} tried to login via /auth/superadmin/login with role {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуется роль суперадминистратора"
        )

    logger.info(f"Superadmin {user.email} logged in successfully")
    return _generate_token_response(user)
