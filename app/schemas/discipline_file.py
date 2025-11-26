from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ========== Request Schemas ==========

class DisciplineFileUpload(BaseModel):
    """Схема для загрузки файла к дисциплине"""
    discipline_id: int = Field(..., gt=0, description="ID дисциплины")
    filename: str = Field(..., min_length=1, max_length=255, description="Имя файла")
    file_type: str = Field(..., description="Тип файла: pdf, doc, docx, ppt, pptx")


# ========== Response Schemas ==========

class DisciplineFileResponse(BaseModel):
    """Ответ с информацией о файле дисциплины"""
    id: int
    discipline_id: int
    filename: str
    file_path: str
    file_type: str
    file_size: int  # в байтах
    uploaded_by: int
    uploader_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DisciplineWithFilesResponse(BaseModel):
    """Дисциплина со списком файлов"""
    id: int
    subject: str
    grade: int
    displayName: str
    files: list[DisciplineFileResponse]
    teacher_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
