from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    student = "student"
    teacher = "teacher"

class RequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class RegistrationRequestCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: RoleEnum
    school_id: int

class IndependentRegistrationRequest(BaseModel):
    """Схема для самостоятельной регистрации без указания школы"""
    full_name: str
    email: EmailStr
    password: str
    role: RoleEnum
    school_id: Optional[int] = None

class RegistrationRequestOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    status: RequestStatus
    school_id: Optional[int] = None  # ← Nullable для индивидуальных

    class Config:
        from_attributes = True  # ✅ для SQLAlchemy → Pydantic
