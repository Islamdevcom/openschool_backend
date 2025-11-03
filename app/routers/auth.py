from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.user import User, RoleEnum
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


def _generate_token_response(user: User) -> dict:
    """Общая функция генерации ответа с токеном"""
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "email": user.email,
        "full_name": user.full_name,
        "school_id": user.school_id
    }


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Вход для УЧИТЕЛЕЙ и СТУДЕНТОВ

    Для администраторов используйте:
    - /auth/admin/login (школьные администраторы)
    - /auth/superadmin/login (суперадминистраторы)
    """
    logger.info(f"Login attempt for email: {request.email}")

    user = _authenticate_user(request.email, request.password, db)

    # Проверяем что это teacher или student
    if user.role not in [RoleEnum.teacher, RoleEnum.student]:
        logger.warning(f"User {user.email} tried to login via /auth/login with role {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Используйте специальный вход для администраторов"
        )

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
