from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class TeacherStudentRelation(Base):
    __tablename__ = "teacher_student_relations"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="students")
    student = relationship("User", foreign_keys=[student_id], back_populates="teachers")