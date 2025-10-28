from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class RequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class RegistrationRequest(Base):
    
    __tablename__ = "register_requests"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.pending)
    school_id = Column(Integer, ForeignKey("schools.id"))
    school = relationship("School", back_populates="requests")
