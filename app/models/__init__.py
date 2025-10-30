from app.database import Base

# Импортируем все модели для Alembic
from app.models.user import User, RoleEnum
from app.models.school import School
from app.models.teacher_student_relation import TeacherStudentRelation
from app.models.registration_request import RegistrationRequest, RequestStatus
from app.models.invite_code import InviteCode
from app.models.student import Student
from app.models.student_activity import StudentActivity

__all__ = [
    "Base",
    "User",
    "RoleEnum",
    "School",
    "TeacherStudentRelation",
    "RegistrationRequest",
    "RequestStatus",
    "InviteCode",
    "Student",
    "StudentActivity",
]