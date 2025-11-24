# app/schemas/tools.py
"""
Pydantic схемы для всех 26 AI-инструментов учителя.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
from enum import Enum


# ============================================================================
# БАЗОВЫЕ СХЕМЫ
# ============================================================================

class ToolResponse(BaseModel):
    """Базовый ответ от инструмента"""
    success: bool
    tool_type: str
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    generation_time_ms: Optional[int] = None


class DifficultyLevel(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class DiscussionType(str, Enum):
    general = "general"
    debate = "debate"
    socratic = "socratic"
    think_pair_share = "think_pair_share"


class EngagementStyle(str, Enum):
    question = "question"
    story = "story"
    video = "video"
    activity = "activity"
    demonstration = "demonstration"
    interactive = "interactive"


class MaterialType(str, Enum):
    worksheet = "worksheet"
    handout = "handout"
    slides = "slides"
    notes = "notes"
    summary = "summary"


class QuestionType(str, Enum):
    multiple_choice = "multiple_choice"
    short_answer = "short_answer"
    essay = "essay"
    true_false = "true_false"
    matching = "matching"
    mixed = "mixed"


class ReportType(str, Enum):
    student_progress = "student_progress"
    class_analytics = "class_analytics"
    grades_summary = "grades_summary"
    attendance = "attendance"
    behavior = "behavior"


# ============================================================================
# 1. ПЛАНИРОВАНИЕ УРОКА
# ============================================================================

class LessonPlanRequest(BaseModel):
    """Запрос на генерацию плана урока"""
    subject: str = Field(..., description="Предмет", min_length=1)
    topic: str = Field(..., description="Тема урока", min_length=1)
    grade: str = Field(..., description="Класс (например, '7' или '7-8')")
    duration: int = Field(45, description="Длительность урока в минутах", ge=15, le=180)
    additional_requirements: Optional[str] = Field(None, description="Дополнительные требования")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Математика",
                "topic": "Теорема Пифагора",
                "grade": "8",
                "duration": 45,
                "additional_requirements": "Включить практические задачи"
            }
        }


# ============================================================================
# 2. ЦЕЛИ ОБУЧЕНИЯ
# ============================================================================

class LearningObjectivesRequest(BaseModel):
    """Запрос на генерацию целей обучения"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Физика",
                "topic": "Законы Ньютона",
                "grade": "9"
            }
        }


# ============================================================================
# 3. РАСПИСАНИЕ
# ============================================================================

class ScheduleRequest(BaseModel):
    """Запрос на генерацию расписания"""
    grade: str = Field(..., description="Класс")
    period: str = Field(..., description="Период (неделя, месяц)")
    subjects: List[str] = Field(..., description="Список предметов", min_items=1)
    constraints: Optional[str] = Field(None, description="Ограничения (например, 'Физкультура не в понедельник')")

    class Config:
        json_schema_extra = {
            "example": {
                "grade": "7",
                "period": "неделя",
                "subjects": ["Математика", "Русский язык", "Физика", "История"],
                "constraints": "Математика - первым уроком"
            }
        }


# ============================================================================
# 4. УЧЕБНЫЕ МАТЕРИАЛЫ
# ============================================================================

class MaterialsRequest(BaseModel):
    """Запрос на генерацию учебных материалов"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    material_type: MaterialType = Field(..., description="Тип материала")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Биология",
                "topic": "Клеточное строение",
                "grade": "6",
                "material_type": "handout"
            }
        }


# ============================================================================
# 5. РАБОЧИЕ ЛИСТЫ
# ============================================================================

class WorksheetRequest(BaseModel):
    """Запрос на генерацию рабочего листа"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    num_tasks: int = Field(10, description="Количество заданий", ge=1, le=30)
    difficulty: DifficultyLevel = Field(DifficultyLevel.medium, description="Сложность")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Математика",
                "topic": "Дроби",
                "grade": "5",
                "num_tasks": 10,
                "difficulty": "medium"
            }
        }


# ============================================================================
# 6. ТЕСТЫ/ВИКТОРИНЫ
# ============================================================================

class QuizRequest(BaseModel):
    """Запрос на генерацию теста/викторины"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    num_questions: int = Field(10, description="Количество вопросов", ge=1, le=50)
    difficulty: DifficultyLevel = Field(DifficultyLevel.medium, description="Сложность")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "История",
                "topic": "Древний Египет",
                "grade": "5",
                "num_questions": 15,
                "difficulty": "easy"
            }
        }


# ============================================================================
# 7. ПРЕЗЕНТАЦИИ
# ============================================================================

class PresentationRequest(BaseModel):
    """Запрос на генерацию презентации"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    num_slides: int = Field(10, description="Количество слайдов", ge=3, le=30)

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "География",
                "topic": "Климатические пояса",
                "grade": "7",
                "num_slides": 12
            }
        }


# ============================================================================
# 8. ОЦЕНИВАНИЕ
# ============================================================================

class AssessmentRequest(BaseModel):
    """Запрос на оценивание работы"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    criteria: str = Field(..., description="Критерии оценивания")
    student_work: str = Field(..., description="Работа ученика", min_length=10)

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Литература",
                "topic": "Анализ стихотворения",
                "criteria": "Понимание темы, аргументация, грамотность",
                "student_work": "Текст работы ученика..."
            }
        }


# ============================================================================
# 9. РУБРИКИ ОЦЕНИВАНИЯ
# ============================================================================

class RubricRequest(BaseModel):
    """Запрос на генерацию рубрики"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    assignment_type: str = Field(..., description="Тип задания (эссе, проект, презентация)")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Русский язык",
                "topic": "Сочинение-рассуждение",
                "grade": "9",
                "assignment_type": "эссе"
            }
        }


# ============================================================================
# 10. КЛЮЧ ОТВЕТОВ
# ============================================================================

class AnswerKeyRequest(BaseModel):
    """Запрос на генерацию ключа ответов"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    questions: str = Field(..., description="Вопросы (в текстовом формате)")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Математика",
                "topic": "Квадратные уравнения",
                "questions": "1. Решите: x^2 - 5x + 6 = 0\n2. Найдите корни: 2x^2 + 3x - 2 = 0"
            }
        }


# ============================================================================
# 11. СТРАТЕГИИ ПРЕПОДАВАНИЯ
# ============================================================================

class TeachingStrategyRequest(BaseModel):
    """Запрос на генерацию стратегий преподавания"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    class_profile: Optional[str] = Field(None, description="Особенности класса")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Химия",
                "topic": "Химические реакции",
                "grade": "8",
                "class_profile": "Активный класс, любят эксперименты"
            }
        }


# ============================================================================
# 12. ВОПРОСЫ ДЛЯ ОБСУЖДЕНИЯ
# ============================================================================

class DiscussionPromptsRequest(BaseModel):
    """Запрос на генерацию вопросов для обсуждения"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    discussion_type: DiscussionType = Field(DiscussionType.general, description="Тип дискуссии")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Обществознание",
                "topic": "Права человека",
                "grade": "10",
                "discussion_type": "debate"
            }
        }


# ============================================================================
# 13. ИНТЕРАКТИВНЫЕ АКТИВНОСТИ
# ============================================================================

class InteractiveActivitiesRequest(BaseModel):
    """Запрос на генерацию интерактивных активностей"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    num_students: int = Field(25, description="Количество учеников", ge=1, le=40)
    duration: int = Field(15, description="Время на активность (минуты)", ge=5, le=45)

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Английский язык",
                "topic": "Present Perfect",
                "grade": "7",
                "num_students": 28,
                "duration": 20
            }
        }


# ============================================================================
# 14. АНАЛИТИКА УЧЕНИКА
# ============================================================================

class StudentAnalyticsRequest(BaseModel):
    """Запрос на анализ успеваемости ученика"""
    student_data: str = Field(..., description="Данные об успеваемости ученика")
    period: str = Field(..., description="Период анализа")

    class Config:
        json_schema_extra = {
            "example": {
                "student_data": "Оценки: Математика [5,4,5,4], Физика [4,4,3,4], посещаемость 95%",
                "period": "1 четверть"
            }
        }


# ============================================================================
# 15. АНАЛИТИКА КЛАССА
# ============================================================================

class ClassAnalyticsRequest(BaseModel):
    """Запрос на анализ успеваемости класса"""
    subject: str = Field(..., description="Предмет")
    class_data: str = Field(..., description="Данные класса")
    period: str = Field(..., description="Период анализа")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Математика",
                "class_data": "Средний балл: 4.2, отличников: 5, хорошистов: 15, троечников: 8",
                "period": "2 четверть"
            }
        }


# ============================================================================
# 16. ОТСЛЕЖИВАНИЕ ПРОГРЕССА
# ============================================================================

class ProgressTrackingRequest(BaseModel):
    """Запрос на отслеживание прогресса"""
    progress_data: str = Field(..., description="Данные о прогрессе")
    goals: str = Field(..., description="Цели ученика")

    class Config:
        json_schema_extra = {
            "example": {
                "progress_data": "Начальный уровень: 60%, текущий: 78%, темы пройдены: 5 из 10",
                "goals": "Достичь 90% к концу четверти"
            }
        }


# ============================================================================
# 17. БИБЛИОТЕКА РЕСУРСОВ
# ============================================================================

class ResourceLibraryRequest(BaseModel):
    """Запрос на поиск ресурсов"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    resource_type: Optional[str] = Field("all", description="Тип ресурса (video, article, book, all)")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Физика",
                "topic": "Электричество",
                "grade": "8",
                "resource_type": "video"
            }
        }


# ============================================================================
# 18. УПРАВЛЕНИЕ ДОКУМЕНТАМИ
# ============================================================================

class DocumentSummaryRequest(BaseModel):
    """Запрос на создание краткого содержания документа"""
    document_content: str = Field(..., description="Содержимое документа", min_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "document_content": "Текст учебного материала или статьи для анализа..."
            }
        }


# ============================================================================
# 19. ПРОВЕРКА ДЗ
# ============================================================================

class HomeworkCheckRequest(BaseModel):
    """Запрос на проверку домашнего задания"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    assignment: str = Field(..., description="Текст задания")
    student_answers: str = Field(..., description="Ответы ученика")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Математика",
                "topic": "Системы уравнений",
                "assignment": "Решите систему: x + y = 5, x - y = 1",
                "student_answers": "x = 3, y = 2"
            }
        }


# ============================================================================
# 20. СОЗДАНИЕ ДЗ
# ============================================================================

class HomeworkGeneratorRequest(BaseModel):
    """Запрос на генерацию домашнего задания"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    difficulty: DifficultyLevel = Field(DifficultyLevel.medium, description="Сложность")
    estimated_time: str = Field("30 минут", description="Примерное время выполнения")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Русский язык",
                "topic": "Причастный оборот",
                "grade": "7",
                "difficulty": "medium",
                "estimated_time": "40 минут"
            }
        }


# ============================================================================
# 21. ТЕСТЫ С ВАРИАНТАМИ
# ============================================================================

class MCQTestRequest(BaseModel):
    """Запрос на генерацию теста с множественным выбором"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    num_questions: int = Field(10, description="Количество вопросов", ge=5, le=30)

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Биология",
                "topic": "Пищеварительная система",
                "grade": "8",
                "num_questions": 15
            }
        }


# ============================================================================
# 22. БАНК ВОПРОСОВ
# ============================================================================

class QuestionBankRequest(BaseModel):
    """Запрос на генерацию банка вопросов"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    num_questions: int = Field(20, description="Количество вопросов", ge=5, le=50)
    question_types: QuestionType = Field(QuestionType.mixed, description="Типы вопросов")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "История",
                "topic": "Великая Отечественная война",
                "grade": "9",
                "num_questions": 25,
                "question_types": "mixed"
            }
        }


# ============================================================================
# 23. ГЕНЕРАЦИЯ ОТЧЕТОВ
# ============================================================================

class ReportGeneratorRequest(BaseModel):
    """Запрос на генерацию отчета"""
    report_type: ReportType = Field(..., description="Тип отчета")
    period: str = Field(..., description="Период")
    data: str = Field(..., description="Данные для отчета")

    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "class_analytics",
                "period": "1 полугодие 2024",
                "data": "7А класс: 28 учеников, средний балл 4.1, посещаемость 94%"
            }
        }


# ============================================================================
# 24. ОТЧЕТ ОБ ОЦЕНКАХ
# ============================================================================

class GradeReportRequest(BaseModel):
    """Запрос на генерацию отчета об оценках"""
    grades_data: str = Field(..., description="Данные об оценках")
    period: str = Field(..., description="Период")

    class Config:
        json_schema_extra = {
            "example": {
                "grades_data": "Иванов: 5,4,5; Петров: 4,4,4; Сидоров: 3,4,3",
                "period": "Ноябрь 2024"
            }
        }


# ============================================================================
# 25. ЗАЦЕПКА УРОКА
# ============================================================================

class LessonHookRequest(BaseModel):
    """Запрос на генерацию зацепки урока"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    engagement_style: EngagementStyle = Field(EngagementStyle.interactive, description="Стиль вовлечения")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Физика",
                "topic": "Закон всемирного тяготения",
                "grade": "9",
                "engagement_style": "demonstration"
            }
        }


# ============================================================================
# 26. ДИФФЕРЕНЦИАЦИЯ
# ============================================================================

class DifferentiationRequest(BaseModel):
    """Запрос на генерацию дифференцированных заданий"""
    subject: str = Field(..., description="Предмет")
    topic: str = Field(..., description="Тема")
    grade: str = Field(..., description="Класс")
    base_content: str = Field(..., description="Базовое содержание/задание")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Математика",
                "topic": "Квадратные уравнения",
                "grade": "8",
                "base_content": "Решение квадратных уравнений через дискриминант"
            }
        }


# ============================================================================
# СХЕМЫ ДЛЯ СОХРАНЕНИЯ В ЖУРНАЛ
# ============================================================================

class SaveToJournalRequest(BaseModel):
    """Запрос на сохранение результата в журнал"""
    tool_type: str = Field(..., description="Тип инструмента")
    topic: str = Field(..., description="Тема")
    student_ids: List[int] = Field(..., description="ID учеников", min_items=1)
    generated_content: str = Field(..., description="Сгенерированный контент")
    lesson_date: Optional[date] = Field(None, description="Дата урока")

    class Config:
        json_schema_extra = {
            "example": {
                "tool_type": "lesson_plan",
                "topic": "Теорема Пифагора",
                "student_ids": [1, 2, 3],
                "generated_content": "План урока...",
                "lesson_date": "2024-11-24"
            }
        }
