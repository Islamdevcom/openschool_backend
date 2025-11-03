from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from ..database import get_db
from ..models.user import User, RoleEnum
from ..auth.hashing import get_password_hash
from ..auth.jwt_handler import create_access_token
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/init", tags=["initialization"])


# ========== Schemas ==========

class CreateFirstSuperadminRequest(BaseModel):
    """Запрос на создание первого суперадминистратора"""
    full_name: str = Field(..., min_length=2, max_length=100, description="Полное имя")
    email: EmailStr = Field(..., description="Email адрес")
    password: str = Field(..., min_length=6, description="Пароль (минимум 6 символов)")

    model_config = {"extra": "ignore"}


class CreateFirstSuperadminResponse(BaseModel):
    """Ответ при создании первого суперадминистратора"""
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    full_name: str
    user_id: int
    message: str

    model_config = {"from_attributes": True}


# ========== Endpoints ==========

@router.post("/create-first-superadmin", status_code=status.HTTP_201_CREATED, response_model=CreateFirstSuperadminResponse)
def create_first_superadmin(
    request_data: CreateFirstSuperadminRequest,
    db: Session = Depends(get_db)
):
    """
    Создать ПЕРВОГО суперадминистратора системы

    ⚠️ ВАЖНО: Этот endpoint работает ТОЛЬКО ОДИН РАЗ!

    После создания первого superadmin этот endpoint блокируется
    и возвращает ошибку 403 для безопасности.

    Используйте этот endpoint сразу после первого деплоя на Railway
    для создания главного администратора системы.

    **Требования:**
    - full_name: Полное имя (минимум 2 символа)
    - email: Email адрес (уникальный)
    - password: Пароль (минимум 6 символов)

    **После создания:**
    - Автоматически выполняется вход
    - Возвращается access_token
    - Endpoint больше НЕ работает (безопасность)

    **Пример запроса:**
    ```json
    {
        "full_name": "Иван Иванов",
        "email": "admin@myschool.com",
        "password": "secure_password_123"
    }
    ```
    """
    logger.info(f"Attempt to create first superadmin for email: {request_data.email}")

    # Проверяем что в системе ещё НЕТ ни одного superadmin
    existing_superadmins = db.query(User).filter(User.role == RoleEnum.superadmin).count()

    if existing_superadmins > 0:
        logger.warning(f"Blocked attempt to create superadmin - {existing_superadmins} superadmin(s) already exist")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Суперадминистратор уже существует. Этот endpoint работает только один раз при первой инициализации системы."
        )

    # Проверяем что email уникален
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    # Хешируем пароль
    hashed_password = get_password_hash(request_data.password)

    # Создаем первого суперадминистратора
    new_superadmin = User(
        full_name=request_data.full_name,
        email=request_data.email,
        hashed_password=hashed_password,
        role=RoleEnum.superadmin,
        school_id=None,  # Суперадмин не привязан к школе
        is_verified=True  # Автоматически верифицирован
    )

    try:
        db.add(new_superadmin)
        db.commit()
        db.refresh(new_superadmin)

        logger.info(f"✅ FIRST SUPERADMIN CREATED: {new_superadmin.email} (ID: {new_superadmin.id})")
        logger.warning(f"🔒 /init/create-first-superadmin endpoint is now BLOCKED")

        # Генерируем токен для автоматического входа
        access_token = create_access_token(data={
            "sub": str(new_superadmin.id),
            "role": new_superadmin.role.value
        })

        return CreateFirstSuperadminResponse(
            access_token=access_token,
            token_type="bearer",
            role=new_superadmin.role.value,
            email=new_superadmin.email,
            full_name=new_superadmin.full_name,
            user_id=new_superadmin.id,
            message="Первый суперадминистратор успешно создан! Этот endpoint теперь заблокирован."
        )

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database error during superadmin creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании суперадминистратора"
        )
