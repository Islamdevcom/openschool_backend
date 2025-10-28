from pydantic import BaseModel, EmailStr
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

class RegistrationRequestOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    status: RequestStatus
    school_id: int

    class Config:
        from_attributes = True  # ✅ для SQLAlchemy → Pydantic
