from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from typing import List

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User, RoleEnum
from ..models.school import School
from ..auth.hashing import get_password_hash
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/superadmin", tags=["superadmin"])


def ensure_superadmin(user: User):
    """Проверка что пользователь - суперадминистратор"""
    if user.role != RoleEnum.superadmin:
        logger.warning(f"Access denied for user {user.id} with role {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуется роль SUPERADMIN"
        )


# ========== Schemas ==========

class CreateSchoolAdminRequest(BaseModel):
    """Создание администратора школы суперадмином"""
    full_name: str = Field(..., min_length=2, max_length=100, description="Полное имя")
    email: EmailStr = Field(..., description="Email адрес")
    password: str = Field(..., min_length=4, description="Пароль")
    school_id: int = Field(..., gt=0, description="ID школы")

    model_config = {"extra": "ignore"}


class CreateSchoolAdminResponse(BaseModel):
    """Ответ при создании администратора школы"""
    user_id: int
    full_name: str
    email: str
    role: str
    school_id: int
    school_name: str
    message: str

    model_config = {"from_attributes": True}


class SchoolListItem(BaseModel):
    """Информация о школе в списке"""
    id: int
    name: str
    code: str

    model_config = {"from_attributes": True}


class CreateSchoolRequest(BaseModel):
    """Создание школы"""
    name: str = Field(..., min_length=2, max_length=200, description="Название школы")
    code: str = Field(..., min_length=4, max_length=20, description="Код школы (7 символов)")

    model_config = {"extra": "ignore"}


class CreateSchoolResponse(BaseModel):
    """Ответ при создании школы"""
    id: int
    name: str
    code: str
    message: str

    model_config = {"from_attributes": True}


# ========== Endpoints ==========

@router.post("/create-school-admin", status_code=status.HTTP_201_CREATED, response_model=CreateSchoolAdminResponse)
def create_school_admin(
    request_data: CreateSchoolAdminRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создать администратора школы (только для суперадмина)

    Суперадминистратор создаёт школьного администратора по ID школы.

    **Требования:**
    - full_name: Полное имя
    - email: Email (уникальный)
    - password: Пароль (минимум 4 символа)
    - school_id: ID школы

    **Пример:**
    ```json
    {
        "full_name": "Мария Иванова",
        "email": "maria@school125.edu",
        "password": "secure_pass",
        "school_id": 12
    }
    ```
    """
    ensure_superadmin(current_user)
    logger.info(f"Superadmin {current_user.id} creating school admin for email: {request_data.email}")

    # Проверяем что email уникален
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    # Проверяем что школа существует
    school = db.query(School).filter(School.id == request_data.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Школа с ID {request_data.school_id} не найдена"
        )

    # Хешируем пароль
    hashed_password = get_password_hash(request_data.password)

    # Создаем администратора школы
    new_admin = User(
        full_name=request_data.full_name,
        email=request_data.email,
        hashed_password=hashed_password,
        role=RoleEnum.school_admin,
        school_id=school.id,
        is_verified=True
    )

    try:
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        logger.info(f"School admin created: {new_admin.email} (ID: {new_admin.id}) for school {school.name}")

        return CreateSchoolAdminResponse(
            user_id=new_admin.id,
            full_name=new_admin.full_name,
            email=new_admin.email,
            role=new_admin.role.value,
            school_id=school.id,
            school_name=school.name,
            message=f"Администратор школы успешно создан для {school.name}"
        )

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database error during school admin creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании администратора школы"
        )


@router.get("/schools", response_model=dict)
def get_all_schools(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить список всех школ (только для суперадмина)

    Возвращает список всех школ в системе с их ID, названиями и кодами.

    **Response:**
    ```json
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "name": "МАОУ Гимназия №125",
                "code": "SCHO125"
            }
        ]
    }
    ```
    """
    ensure_superadmin(current_user)
    logger.info(f"Superadmin {current_user.id} requesting all schools")

    schools = db.query(School).order_by(School.name).all()

    schools_data = [
        SchoolListItem(
            id=school.id,
            name=school.name,
            code=school.code
        ).model_dump()
        for school in schools
    ]

    logger.info(f"Returning {len(schools_data)} schools")

    return {
        "success": True,
        "data": schools_data
    }


@router.post("/create-school", status_code=status.HTTP_201_CREATED, response_model=CreateSchoolResponse)
def create_school(
    request_data: CreateSchoolRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создать новую школу (только для суперадмина)

    **Требования:**
    - name: Название школы (уникальное)
    - code: Код школы (уникальный, 7 символов рекомендуется)

    **Пример:**
    ```json
    {
        "name": "МАОУ Гимназия №125",
        "code": "SCHO125"
    }
    ```
    """
    ensure_superadmin(current_user)
    logger.info(f"Superadmin {current_user.id} creating school: {request_data.name}")

    # Проверяем уникальность названия
    existing_name = db.query(School).filter(School.name == request_data.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Школа с таким названием уже существует"
        )

    # Проверяем уникальность кода
    existing_code = db.query(School).filter(School.code == request_data.code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Школа с таким кодом уже существует"
        )

    # Создаем школу
    new_school = School(
        name=request_data.name,
        code=request_data.code
    )

    try:
        db.add(new_school)
        db.commit()
        db.refresh(new_school)

        logger.info(f"School created: {new_school.name} (ID: {new_school.id}, code: {new_school.code})")

        return CreateSchoolResponse(
            id=new_school.id,
            name=new_school.name,
            code=new_school.code,
            message="Школа успешно создана"
        )

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database error during school creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании школы"
        )
