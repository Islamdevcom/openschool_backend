from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DisciplineFile(Base):
    """
    Файлы (книжки, материалы) для дисциплин

    Админ школы может загружать PDF, DOC, PPT файлы для каждого предмета
    """
    __tablename__ = "discipline_files"

    id = Column(Integer, primary_key=True, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)  # Оригинальное имя файла
    file_path = Column(String(500), nullable=False)  # Путь к файлу на сервере
    file_type = Column(String(50), nullable=False)  # pdf, doc, docx, ppt, pptx
    file_size = Column(BigInteger, nullable=False)  # Размер в байтах
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто загрузил (админ)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    discipline = relationship("Discipline", back_populates="files")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<DisciplineFile(id={self.id}, filename={self.filename}, discipline_id={self.discipline_id})>"
