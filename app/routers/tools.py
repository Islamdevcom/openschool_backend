# app/routers/tools.py
"""
Роутер для всех 26 AI-инструментов учителя.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, RoleEnum
from app.models.generated_content import GeneratedContent, ToolUsageLog

# Импорт схем
from app.schemas.tools import (
    ToolResponse,
    LessonPlanRequest,
    LearningObjectivesRequest,
    ScheduleRequest,
    MaterialsRequest,
    WorksheetRequest,
    QuizRequest,
    PresentationRequest,
    AssessmentRequest,
    RubricRequest,
    AnswerKeyRequest,
    TeachingStrategyRequest,
    DiscussionPromptsRequest,
    InteractiveActivitiesRequest,
    StudentAnalyticsRequest,
    ClassAnalyticsRequest,
    ProgressTrackingRequest,
    ResourceLibraryRequest,
    DocumentSummaryRequest,
    HomeworkCheckRequest,
    HomeworkGeneratorRequest,
    MCQTestRequest,
    QuestionBankRequest,
    ReportGeneratorRequest,
    GradeReportRequest,
    LessonHookRequest,
    DifferentiationRequest,
    SaveToJournalRequest,
)

# Импорт сервиса OpenAI
from app.services.openai_service import (
    generate_lesson_plan,
    generate_learning_objectives,
    generate_schedule,
    generate_materials,
    generate_worksheet,
    generate_quiz,
    generate_presentation,
    evaluate_student_work,
    generate_rubric,
    generate_answer_key,
    generate_teaching_strategy,
    generate_discussion_prompts,
    generate_interactive_activities,
    analyze_student_performance,
    analyze_class_performance,
    track_progress,
    search_resources,
    summarize_document,
    check_homework,
    generate_homework,
    generate_mcq_test,
    generate_question_bank,
    generate_report,
    generate_grade_report,
    generate_lesson_hook,
    generate_differentiation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["AI Tools"])


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def check_teacher_role(user: User):
    """Проверка что пользователь - учитель или админ"""
    allowed_roles = [RoleEnum.teacher, RoleEnum.school_admin, RoleEnum.superadmin]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Доступ разрешен только учителям и администраторам"
        )


async def log_tool_usage(
    db: Session,
    user: User,
    tool_type: str,
    request_params: Dict[str, Any],
    success: bool,
    tokens_used: int = 0,
    response_time_ms: int = 0,
    error_message: str = None
):
    """Логирование использования инструмента"""
    try:
        log_entry = ToolUsageLog(
            teacher_id=user.id,
            school_id=user.school_id,
            tool_type=tool_type,
            request_params=request_params,
            success=1 if success else 0,
            error_message=error_message,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Error logging tool usage: {e}")


async def save_generated_content(
    db: Session,
    user: User,
    tool_type: str,
    content: Dict[str, Any],
    subject: str = None,
    topic: str = None,
    grade_level: str = None,
    tokens_used: int = 0,
    generation_time_ms: int = 0
) -> int:
    """Сохранение сгенерированного контента"""
    try:
        entry = GeneratedContent(
            teacher_id=user.id,
            school_id=user.school_id,
            tool_type=tool_type,
            subject=subject,
            topic=topic,
            grade_level=grade_level,
            content=content,
            content_text=str(content)[:5000],
            tokens_used=tokens_used,
            generation_time_ms=generation_time_ms
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry.id
    except Exception as e:
        logger.error(f"Error saving generated content: {e}")
        return None


def create_response(
    tool_type: str,
    result: Dict[str, Any]
) -> ToolResponse:
    """Создание стандартного ответа"""
    if result.get("success"):
        return ToolResponse(
            success=True,
            tool_type=tool_type,
            content=result.get("content"),
            tokens_used=result.get("tokens_used"),
            generation_time_ms=result.get("generation_time_ms")
        )
    else:
        return ToolResponse(
            success=False,
            tool_type=tool_type,
            error=result.get("error", "Неизвестная ошибка"),
            tokens_used=result.get("tokens_used"),
            generation_time_ms=result.get("generation_time_ms")
        )


# ============================================================================
# ENDPOINTS ДЛЯ ИНСТРУМЕНТОВ
# ============================================================================

# 1. ПЛАНИРОВАНИЕ УРОКА
@router.post("/lesson-plan", response_model=ToolResponse)
async def create_lesson_plan(
    request: LessonPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация плана урока.

    Создает структурированный план урока с целями, активностями и оцениванием.
    """
    check_teacher_role(current_user)

    result = await generate_lesson_plan(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        duration=request.duration,
        additional_requirements=request.additional_requirements or ""
    )

    await log_tool_usage(
        db, current_user, "lesson_plan",
        request.model_dump(),
        result.get("success", False),
        result.get("tokens_used", 0),
        result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "lesson_plan",
            result.get("content"),
            request.subject, request.topic, request.grade,
            result.get("tokens_used", 0),
            result.get("generation_time_ms", 0)
        )

    return create_response("lesson_plan", result)


# 2. ЦЕЛИ ОБУЧЕНИЯ
@router.post("/learning-objectives", response_model=ToolResponse)
async def create_learning_objectives(
    request: LearningObjectivesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация целей обучения.

    Создает SMART цели обучения по таксономии Блума.
    """
    check_teacher_role(current_user)

    result = await generate_learning_objectives(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade
    )

    await log_tool_usage(
        db, current_user, "learning_objectives",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("learning_objectives", result)


# 3. РАСПИСАНИЕ
@router.post("/schedule", response_model=ToolResponse)
async def create_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация расписания уроков.
    """
    check_teacher_role(current_user)

    result = await generate_schedule(
        grade=request.grade,
        period=request.period,
        subjects=request.subjects,
        constraints=request.constraints or ""
    )

    await log_tool_usage(
        db, current_user, "schedule",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("schedule", result)


# 4. УЧЕБНЫЕ МАТЕРИАЛЫ
@router.post("/materials", response_model=ToolResponse)
async def create_materials(
    request: MaterialsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация учебных материалов.
    """
    check_teacher_role(current_user)

    result = await generate_materials(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        material_type=request.material_type.value
    )

    await log_tool_usage(
        db, current_user, "materials",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "materials",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("materials", result)


# 5. РАБОЧИЕ ЛИСТЫ
@router.post("/worksheet", response_model=ToolResponse)
async def create_worksheet(
    request: WorksheetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация рабочего листа.
    """
    check_teacher_role(current_user)

    result = await generate_worksheet(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        num_tasks=request.num_tasks,
        difficulty=request.difficulty.value
    )

    await log_tool_usage(
        db, current_user, "worksheet",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "worksheet",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("worksheet", result)


# 6. ТЕСТЫ/ВИКТОРИНЫ
@router.post("/quiz", response_model=ToolResponse)
async def create_quiz(
    request: QuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация теста или викторины.
    """
    check_teacher_role(current_user)

    result = await generate_quiz(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        num_questions=request.num_questions,
        difficulty=request.difficulty.value
    )

    await log_tool_usage(
        db, current_user, "quiz",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "quiz",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("quiz", result)


# 7. ПРЕЗЕНТАЦИИ
@router.post("/presentation", response_model=ToolResponse)
async def create_presentation(
    request: PresentationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация структуры презентации.
    """
    check_teacher_role(current_user)

    result = await generate_presentation(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        num_slides=request.num_slides
    )

    await log_tool_usage(
        db, current_user, "presentation",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "presentation",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("presentation", result)


# 8. ОЦЕНИВАНИЕ
@router.post("/assessment", response_model=ToolResponse)
async def create_assessment(
    request: AssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Оценивание работы ученика с AI.
    """
    check_teacher_role(current_user)

    result = await evaluate_student_work(
        subject=request.subject,
        topic=request.topic,
        criteria=request.criteria,
        student_work=request.student_work
    )

    await log_tool_usage(
        db, current_user, "assessment",
        {"subject": request.subject, "topic": request.topic},
        result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("assessment", result)


# 9. РУБРИКИ ОЦЕНИВАНИЯ
@router.post("/rubric", response_model=ToolResponse)
async def create_rubric(
    request: RubricRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация рубрики оценивания.
    """
    check_teacher_role(current_user)

    result = await generate_rubric(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        assignment_type=request.assignment_type
    )

    await log_tool_usage(
        db, current_user, "rubric",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "rubric",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("rubric", result)


# 10. КЛЮЧ ОТВЕТОВ
@router.post("/answer-key", response_model=ToolResponse)
async def create_answer_key(
    request: AnswerKeyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация ключа ответов.
    """
    check_teacher_role(current_user)

    result = await generate_answer_key(
        subject=request.subject,
        topic=request.topic,
        questions=request.questions
    )

    await log_tool_usage(
        db, current_user, "answer_key",
        {"subject": request.subject, "topic": request.topic},
        result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("answer_key", result)


# 11. СТРАТЕГИИ ПРЕПОДАВАНИЯ
@router.post("/teaching-strategy", response_model=ToolResponse)
async def create_teaching_strategy(
    request: TeachingStrategyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация стратегий преподавания.
    """
    check_teacher_role(current_user)

    result = await generate_teaching_strategy(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        class_profile=request.class_profile or ""
    )

    await log_tool_usage(
        db, current_user, "teaching_strategy",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("teaching_strategy", result)


# 12. ВОПРОСЫ ДЛЯ ОБСУЖДЕНИЯ
@router.post("/discussion-prompts", response_model=ToolResponse)
async def create_discussion_prompts(
    request: DiscussionPromptsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация вопросов для обсуждения.
    """
    check_teacher_role(current_user)

    result = await generate_discussion_prompts(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        discussion_type=request.discussion_type.value
    )

    await log_tool_usage(
        db, current_user, "discussion_prompts",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("discussion_prompts", result)


# 13. ИНТЕРАКТИВНЫЕ АКТИВНОСТИ
@router.post("/interactive-activities", response_model=ToolResponse)
async def create_interactive_activities(
    request: InteractiveActivitiesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация интерактивных активностей.
    """
    check_teacher_role(current_user)

    result = await generate_interactive_activities(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        num_students=request.num_students,
        duration=request.duration
    )

    await log_tool_usage(
        db, current_user, "interactive_activities",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("interactive_activities", result)


# 14. АНАЛИТИКА УЧЕНИКА
@router.post("/student-analytics", response_model=ToolResponse)
async def create_student_analytics(
    request: StudentAnalyticsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Анализ успеваемости ученика.
    """
    check_teacher_role(current_user)

    result = await analyze_student_performance(
        student_data=request.student_data,
        period=request.period
    )

    await log_tool_usage(
        db, current_user, "student_analytics",
        {"period": request.period}, result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("student_analytics", result)


# 15. АНАЛИТИКА КЛАССА
@router.post("/class-analytics", response_model=ToolResponse)
async def create_class_analytics(
    request: ClassAnalyticsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Анализ успеваемости класса.
    """
    check_teacher_role(current_user)

    result = await analyze_class_performance(
        subject=request.subject,
        class_data=request.class_data,
        period=request.period
    )

    await log_tool_usage(
        db, current_user, "class_analytics",
        {"subject": request.subject, "period": request.period},
        result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("class_analytics", result)


# 16. ОТСЛЕЖИВАНИЕ ПРОГРЕССА
@router.post("/progress-tracking", response_model=ToolResponse)
async def create_progress_tracking(
    request: ProgressTrackingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отслеживание прогресса ученика.
    """
    check_teacher_role(current_user)

    result = await track_progress(
        progress_data=request.progress_data,
        goals=request.goals
    )

    await log_tool_usage(
        db, current_user, "progress_tracking",
        {}, result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("progress_tracking", result)


# 17. БИБЛИОТЕКА РЕСУРСОВ
@router.post("/resource-library", response_model=ToolResponse)
async def search_resource_library(
    request: ResourceLibraryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Поиск образовательных ресурсов.
    """
    check_teacher_role(current_user)

    result = await search_resources(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        resource_type=request.resource_type or "all"
    )

    await log_tool_usage(
        db, current_user, "resource_library",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("resource_library", result)


# 18. УПРАВЛЕНИЕ ДОКУМЕНТАМИ
@router.post("/document-summary", response_model=ToolResponse)
async def create_document_summary(
    request: DocumentSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создание краткого содержания документа.
    """
    check_teacher_role(current_user)

    result = await summarize_document(
        document_content=request.document_content
    )

    await log_tool_usage(
        db, current_user, "document_summary",
        {}, result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("document_summary", result)


# 19. ПРОВЕРКА ДЗ
@router.post("/homework-check", response_model=ToolResponse)
async def check_homework_submission(
    request: HomeworkCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Проверка домашнего задания с AI.
    """
    check_teacher_role(current_user)

    result = await check_homework(
        subject=request.subject,
        topic=request.topic,
        assignment=request.assignment,
        student_answers=request.student_answers
    )

    await log_tool_usage(
        db, current_user, "homework_check",
        {"subject": request.subject, "topic": request.topic},
        result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("homework_check", result)


# 20. СОЗДАНИЕ ДЗ
@router.post("/homework-generator", response_model=ToolResponse)
async def generate_homework_assignment(
    request: HomeworkGeneratorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация домашнего задания.
    """
    check_teacher_role(current_user)

    result = await generate_homework(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        difficulty=request.difficulty.value,
        estimated_time=request.estimated_time
    )

    await log_tool_usage(
        db, current_user, "homework_generator",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "homework",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("homework_generator", result)


# 21. ТЕСТЫ С ВАРИАНТАМИ
@router.post("/mcq-test", response_model=ToolResponse)
async def create_mcq_test(
    request: MCQTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация теста с множественным выбором.
    """
    check_teacher_role(current_user)

    result = await generate_mcq_test(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        num_questions=request.num_questions
    )

    await log_tool_usage(
        db, current_user, "mcq_test",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "mcq_test",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("mcq_test", result)


# 22. БАНК ВОПРОСОВ
@router.post("/question-bank", response_model=ToolResponse)
async def create_question_bank(
    request: QuestionBankRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация банка вопросов.
    """
    check_teacher_role(current_user)

    result = await generate_question_bank(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        num_questions=request.num_questions,
        question_types=request.question_types.value
    )

    await log_tool_usage(
        db, current_user, "question_bank",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "question_bank",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("question_bank", result)


# 23. ГЕНЕРАЦИЯ ОТЧЕТОВ
@router.post("/report-generator", response_model=ToolResponse)
async def generate_management_report(
    request: ReportGeneratorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация отчета для руководства.
    """
    check_teacher_role(current_user)

    result = await generate_report(
        report_type=request.report_type.value,
        period=request.period,
        data=request.data
    )

    await log_tool_usage(
        db, current_user, "report_generator",
        {"report_type": request.report_type.value, "period": request.period},
        result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("report_generator", result)


# 24. ОТЧЕТ ОБ ОЦЕНКАХ
@router.post("/grade-report", response_model=ToolResponse)
async def generate_grades_report(
    request: GradeReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация отчета об оценках.
    """
    check_teacher_role(current_user)

    result = await generate_grade_report(
        grades_data=request.grades_data,
        period=request.period
    )

    await log_tool_usage(
        db, current_user, "grade_report",
        {"period": request.period}, result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    return create_response("grade_report", result)


# 25. ЗАЦЕПКА УРОКА
@router.post("/lesson-hook", response_model=ToolResponse)
async def create_lesson_hook(
    request: LessonHookRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация зацепки урока (увлекательного начала).
    """
    check_teacher_role(current_user)

    result = await generate_lesson_hook(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        engagement_style=request.engagement_style.value
    )

    await log_tool_usage(
        db, current_user, "lesson_hook",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "lesson_hook",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("lesson_hook", result)


# 26. ДИФФЕРЕНЦИАЦИЯ
@router.post("/differentiation", response_model=ToolResponse)
async def create_differentiation(
    request: DifferentiationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация дифференцированных заданий (уровни A, B, C).
    """
    check_teacher_role(current_user)

    result = await generate_differentiation(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade,
        base_content=request.base_content
    )

    await log_tool_usage(
        db, current_user, "differentiation",
        request.model_dump(), result.get("success", False),
        result.get("tokens_used", 0), result.get("generation_time_ms", 0),
        result.get("error")
    )

    if result.get("success"):
        await save_generated_content(
            db, current_user, "differentiation",
            result.get("content"),
            request.subject, request.topic, request.grade
        )

    return create_response("differentiation", result)


# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS
# ============================================================================

@router.get("/history")
async def get_tool_history(
    tool_type: str = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить историю использования инструментов.
    """
    check_teacher_role(current_user)

    query = db.query(GeneratedContent).filter(
        GeneratedContent.teacher_id == current_user.id
    )

    if tool_type:
        query = query.filter(GeneratedContent.tool_type == tool_type)

    results = query.order_by(GeneratedContent.created_at.desc()).limit(limit).all()

    return [
        {
            "id": r.id,
            "tool_type": r.tool_type,
            "subject": r.subject,
            "topic": r.topic,
            "grade_level": r.grade_level,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in results
    ]


@router.get("/history/{content_id}")
async def get_generated_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить сгенерированный контент по ID.
    """
    check_teacher_role(current_user)

    content = db.query(GeneratedContent).filter(
        GeneratedContent.id == content_id,
        GeneratedContent.teacher_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="Контент не найден")

    return {
        "id": content.id,
        "tool_type": content.tool_type,
        "subject": content.subject,
        "topic": content.topic,
        "grade_level": content.grade_level,
        "content": content.content,
        "created_at": content.created_at.isoformat() if content.created_at else None
    }


@router.get("/stats")
async def get_tool_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить статистику использования инструментов.
    """
    check_teacher_role(current_user)

    from sqlalchemy import func

    stats = db.query(
        ToolUsageLog.tool_type,
        func.count(ToolUsageLog.id).label('count'),
        func.sum(ToolUsageLog.tokens_used).label('total_tokens'),
        func.avg(ToolUsageLog.response_time_ms).label('avg_time')
    ).filter(
        ToolUsageLog.teacher_id == current_user.id
    ).group_by(ToolUsageLog.tool_type).all()

    return {
        "tools": [
            {
                "tool_type": s.tool_type,
                "usage_count": s.count,
                "total_tokens": s.total_tokens or 0,
                "avg_response_time_ms": int(s.avg_time) if s.avg_time else 0
            }
            for s in stats
        ],
        "total_usage": sum(s.count for s in stats)
    }
