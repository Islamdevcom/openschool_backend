from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from ..database import Base
import enum

# ✅ Перечисление ролей
class RoleEnum(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    teacher = "teacher"
    student = "student"

# ✅ Модель пользователя
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}  # 🛠️ Чтобы избежать конфликтов при повторной загрузке

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default="student")
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
