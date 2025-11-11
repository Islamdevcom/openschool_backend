from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class StudentStats(Base):
    """
    Таблица статистики ученика
    Хранит средний балл, посещаемость, замечания и оценку поведения
    """
    __tablename__ = "student_stats"

    id = Column(Integer, primary_key=True, index=True)
    student_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    avg_grade = Column(Numeric(3, 2), nullable=True)  # Средний балл (4.3, 3.8)
    attendance = Column(Numeric(5, 2), nullable=True)  # Посещаемость в % (95.5, 88.0)
    warnings = Column(Integer, default=0)  # Количество замечаний
    behavior = Column(Numeric(3, 2), nullable=True)  # Оценка поведения (8.5, 7.2)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Связь с таблицей users
    student = relationship("User", foreign_keys="StudentStats.student_user_id")
