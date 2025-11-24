# app/models/generated_content.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ..database import Base


class GeneratedContent(Base):
    """Модель для хранения сгенерированного AI-контента"""
    __tablename__ = "generated_contents"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)

    # Тип инструмента
    tool_type = Column(String(100), nullable=False)  # lesson_plan, quiz, worksheet и т.д.

    # Параметры запроса
    subject = Column(String(255), nullable=True)
    topic = Column(String(255), nullable=True)
    grade_level = Column(String(50), nullable=True)

    # Сгенерированный контент
    content = Column(JSON, nullable=False)  # JSON с результатом
    content_text = Column(Text, nullable=True)  # Текстовая версия для поиска

    # Метаданные
    language = Column(String(10), default="ru")
    tokens_used = Column(Integer, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ToolUsageLog(Base):
    """Лог использования AI-инструментов"""
    __tablename__ = "tool_usage_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)

    tool_type = Column(String(100), nullable=False)
    request_params = Column(JSON, nullable=True)

    # Результат
    success = Column(Integer, default=1)  # 1 = успех, 0 = ошибка
    error_message = Column(Text, nullable=True)

    # Метрики
    tokens_used = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
