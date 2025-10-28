from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class StudentActivity(Base):
    __tablename__ = "student_activities"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic = Column(String(255), nullable=True)
    ai_score = Column(Integer, nullable=True)  # 0-100
    manual_score = Column(Integer, nullable=True)  # 0-100
    ai_explanation = Column(Text, nullable=True)
    teacher_comment = Column(Text, nullable=True)
    lesson_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())