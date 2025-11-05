from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    address = Column(String, nullable=True)  # Адрес школы
    max_users = Column(Integer, default=500, nullable=False)  # Максимум пользователей
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Дата создания

    # Связи
    users = relationship("User", foreign_keys="User.school_id")
    disciplines = relationship("Discipline", back_populates="school", cascade="all, delete-orphan")
    