from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Discipline(Base):
    """
    Дисциплины (предметы) в школе

    Например: Физика 7 класс, Математика 8 класс, и т.д.
    """
    __tablename__ = "disciplines"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)  # "Математика", "Физика", и т.д.
    grade = Column(Integer, nullable=False)  # класс: 1-11
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    school = relationship("School", back_populates="disciplines")
    teacher_assignments = relationship("TeacherDiscipline", back_populates="discipline", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('grade >= 1 AND grade <= 11', name='check_grade_range'),
        UniqueConstraint('school_id', 'subject', 'grade', name='uq_school_subject_grade'),
    )

    def __repr__(self):
        return f"<Discipline(id={self.id}, subject={self.subject}, grade={self.grade}, school_id={self.school_id})>"
