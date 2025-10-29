from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    
    # Связи
    users = relationship("User", foreign_keys="User.school_id")
    