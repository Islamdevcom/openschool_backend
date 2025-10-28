# backend/app/models/__init__.py

from ..database import Base  # общий Base для всех моделей

# Импортируем все модели, чтобы они регистрировались в Base.metadata
from .user import User
from .school import School
from .registration_request import RegistrationRequest
from .invite_code import InviteCode
from .teacher_student_link import TeacherStudentLink
from .student import Student, StudentTypeEnum
from .student_activity import StudentActivity


__all__ = [
    "Base",
    "User",
    "School",
    "RegistrationRequest",
    "InviteCode",
    "TeacherStudentLink",
]
