from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class RoleEnum(str, enum.Enum):
    teacher = "teacher"
    student = "student"
    school_admin = "school_admin"
    superadmin = "superadmin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    
    # Школа (nullable для independent)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    school = relationship("School")

    # Для учителей - назначенные дисциплины
    assigned_disciplines = relationship("TeacherDiscipline", foreign_keys="TeacherDiscipline.teacher_id", back_populates="teacher")

    
    # Для учителей
    teacher_invite_code = Column(String, unique=True, nullable=True)  # для independent teachers
    
    # Для студентов
    referral_code = Column(String, unique=True, nullable=True)  # код студента для приглашений
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # кто пригласил
    loyalty_points = Column(Integer, default=0)  # баллы лояльности
    
    # Верификация
    is_verified = Column(Boolean, default=False)
    