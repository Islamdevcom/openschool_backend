from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TeacherDiscipline(Base):
    """
    Связь между учителем и дисциплиной

    Показывает какие дисциплины назначены учителю администратором школы
    """
    __tablename__ = "teacher_disciplines"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # админ который назначил
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)  # для мягкого удаления

    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="assigned_disciplines")
    discipline = relationship("Discipline", back_populates="teacher_assignments")
    admin = relationship("User", foreign_keys=[assigned_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint('teacher_id', 'discipline_id', name='uq_teacher_discipline'),
    )

    def __repr__(self):
        return f"<TeacherDiscipline(teacher_id={self.teacher_id}, discipline_id={self.discipline_id}, is_active={self.is_active})>"
