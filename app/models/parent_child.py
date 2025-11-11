from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ParentChild(Base):
    """
    Таблица связи родитель-ребенок
    Связывает родителей (users с role=parent) с детьми (users с role=student)
    """
    __tablename__ = "parent_child"

    id = Column(Integer, primary_key=True, index=True)
    parent_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    relationship = Column(String(50), nullable=True)  # 'father', 'mother', 'guardian'
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Связи с таблицей users
    parent = relationship("User", foreign_keys=[parent_user_id])
    student = relationship("User", foreign_keys=[student_user_id])

    # Уникальное ограничение: один родитель не может быть дважды привязан к одному ребенку
    __table_args__ = (
        UniqueConstraint('parent_user_id', 'student_user_id', name='uq_parent_student'),
    )
