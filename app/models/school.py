from sqlalchemy import Column, Integer, String
from ..database import Base
from app.models.registration_request import RegistrationRequest
from sqlalchemy.orm import relationship
# ✅ Модель школы
class School(Base):
    __tablename__ = "schools"
    __table_args__ = {'extend_existing': True}  # 🛠️ Чтобы не было конфликта при повторном импорте
    
    requests = relationship("RegistrationRequest", back_populates="school")

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
