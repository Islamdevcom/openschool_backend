from app.database import Base

# Импортируем новые модели
from app.models.user import User, RoleEnum
from app.models.school import School
from app.models.teacher_student_relation import TeacherStudentRelation

__all__ = [
    "Base",
    "User",
    "RoleEnum",
    "School",
    "TeacherStudentRelation",
]