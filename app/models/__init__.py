from app.database import Base

# Импортируем все модели для Alembic
from app.models.user import User, RoleEnum
from app.models.school import School
from app.models.teacher_student_relation import TeacherStudentRelation
from app.models.registration_request import RegistrationRequest, RequestStatus
from app.models.invite_code import InviteCode
from app.models.student import Student
from app.models.student_activity import StudentActivity
from app.models.discipline import Discipline
from app.models.teacher_discipline import TeacherDiscipline
from app.models.parent_child import ParentChild
from app.models.student_stats import StudentStats

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
    "Discipline",
    "TeacherDiscipline",
    "ParentChild",
    "StudentStats",
]