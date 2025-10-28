from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from ..database import Base
import enum

class StudentTypeEnum(str, enum.Enum):
    individual = "individual"
    school = "school"

class Student(Base):
    __tablename__ = "students"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    grade = Column(String(50), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    student_type = Column(Enum(StudentTypeEnum), default=StudentTypeEnum.individual)
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)