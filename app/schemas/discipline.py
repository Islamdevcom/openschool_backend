from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


# Маппинг предметов в коды для фронтенда
SUBJECT_CODES = {
    'Математика': 'math',
    'Русский язык': 'russian',
    'Литература': 'literature',
    'Физика': 'physics',
    'Химия': 'chemistry',
    'Биология': 'biology',
    'История': 'history',
    'Обществознание': 'social',
    'География': 'geography',
    'Английский язык': 'english',
    'Немецкий язык': 'german',
    'Французский язык': 'french',
    'Информатика': 'informatics',
    'Физическая культура': 'pe',
    'Музыка': 'music',
    'ИЗО': 'art'
}

# Допустимые предметы
VALID_SUBJECTS = list(SUBJECT_CODES.keys())


def generate_discipline_id(subject: str, grade: int) -> str:
    """Генерирует ID дисциплины для фронтенда (например: physics-7)"""
    code = SUBJECT_CODES.get(subject, subject.lower())
    return f"{code}-{grade}"


# ========== Request Schemas ==========

class DisciplineCreate(BaseModel):
    """Схема для создания дисциплины администратором"""
    subject: str = Field(..., min_length=1, max_length=100, description="Название предмета")
    grade: int = Field(..., ge=1, le=11, description="Класс (1-11)")

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        if v not in VALID_SUBJECTS:
            raise ValueError(
                f"Недопустимый предмет. Допустимые значения: {', '.join(VALID_SUBJECTS)}"
            )
        return v

    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: int) -> int:
        if not (1 <= v <= 11):
            raise ValueError("Класс должен быть от 1 до 11")
        return v


class DisciplineAssign(BaseModel):
    """Схема для назначения дисциплины учителю"""
    discipline_id: int = Field(..., gt=0, description="ID дисциплины")


# ========== Response Schemas ==========

class AssignedByInfo(BaseModel):
    """Информация о том, кто назначил дисциплину"""
    id: int
    name: str

    model_config = {"from_attributes": True}


class DisciplineResponse(BaseModel):
    """Ответ с информацией о дисциплине"""
    id: int
    subject: str
    grade: int
    displayName: str
    school_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_display_name(cls, discipline):
        """Создает response с автоматическим displayName"""
        return cls(
            id=discipline.id,
            subject=discipline.subject,
            grade=discipline.grade,
            displayName=f"{discipline.subject} - {discipline.grade} класс",
            school_id=discipline.school_id,
            created_at=discipline.created_at
        )


class TeacherInfo(BaseModel):
    """Информация об учителе"""
    teacher_id: int
    teacher_name: str
    assigned_at: datetime

    model_config = {"from_attributes": True}


class DisciplineWithTeachers(BaseModel):
    """Дисциплина со списком назначенных учителей (для админа)"""
    id: int
    subject: str
    grade: int
    displayName: str
    assigned_teachers: list[TeacherInfo]
    created_at: datetime

    model_config = {"from_attributes": True}


class TeacherDisciplineResponse(BaseModel):
    """Дисциплина учителя (для учителя)"""
    id: str  # Формат: physics-7
    discipline_id: int
    subject: str
    grade: int
    displayName: str
    assigned_at: datetime
    assigned_by: AssignedByInfo

    model_config = {"from_attributes": True}

    @classmethod
    def from_teacher_discipline(cls, td, admin_name: str):
        """Создает response из TeacherDiscipline модели"""
        return cls(
            id=generate_discipline_id(td.discipline.subject, td.discipline.grade),
            discipline_id=td.discipline.id,
            subject=td.discipline.subject,
            grade=td.discipline.grade,
            displayName=f"{td.discipline.subject} - {td.discipline.grade} класс",
            assigned_at=td.assigned_at,
            assigned_by=AssignedByInfo(
                id=td.assigned_by,
                name=admin_name
            )
        )


class AssignmentResponse(BaseModel):
    """Ответ при назначении дисциплины учителю"""
    teacher_id: int
    teacher_name: str
    discipline: DisciplineResponse
    assigned_by: AssignedByInfo
    assigned_at: datetime


class TeacherDisciplinesInfo(BaseModel):
    """Информация о дисциплинах учителя (для админа)"""
    teacher: dict  # {id, name, email}
    disciplines: list[TeacherDisciplineResponse]


# ========== Teacher Profile Schema ==========

class SchoolInfo(BaseModel):
    """Информация о школе"""
    id: int
    name: str

    model_config = {"from_attributes": True}


class TeacherProfileResponse(BaseModel):
    """Профиль учителя с дисциплинами"""
    id: int
    name: str
    email: str
    school: Optional[SchoolInfo] = None
    assigned_disciplines: list[TeacherDisciplineResponse]
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
