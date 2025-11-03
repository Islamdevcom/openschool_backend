from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = {"extra": "ignore"}


class SchoolAdminRegisterRequest(BaseModel):
    """Регистрация администратора школы"""
    full_name: str = Field(..., min_length=2, max_length=100, description="Полное имя")
    email: EmailStr = Field(..., description="Email адрес")
    password: str = Field(..., min_length=4, description="Пароль")
    school_code: str = Field(..., min_length=4, max_length=20, description="Код школы")

    model_config = {"extra": "ignore"}


class SchoolAdminRegisterResponse(BaseModel):
    """Ответ при регистрации администратора школы"""
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    full_name: str
    school_id: int
    user_id: int

    model_config = {"from_attributes": True}