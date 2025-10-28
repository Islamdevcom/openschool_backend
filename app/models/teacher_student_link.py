from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from ..database import Base

class TeacherStudentLink(Base):
    __tablename__ = "teacher_student_links"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("teacher_id", "student_id", name="uq_teacher_student"),)
