# routers/student.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, distinct
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.database import get_db
from app.dependencies import get_current_user
from app.models.student import Student, StudentTypeEnum
from app.models.student_activity import StudentActivity
from app.models.discipline import Discipline
from app.models.user import User
from app.crud.discipline import get_discipline_teachers
from app.crud.discipline_file import get_discipline_files
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["students"])

# Получить индивидуальных студентов для преподавателя
@router.get("/students")
async def get_individual_students(
    group: Optional[str] = Query(None),
    date: Optional[date] = Query(None),
    period: Optional[str] = Query("last_month"),  # last_week, last_month, last_quarter
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список индивидуальных студентов с их активностями"""
    
    # Только индивидуальные студенты
    query = db.query(Student).filter(
        and_(
            Student.teacher_id == current_user.id,
            Student.student_type == StudentTypeEnum.individual,
            Student.is_active == True
        )
    )
    
    students = query.all()
    
    # Определяем период для фильтрации активностей
    date_filter = None
    if date:
        date_filter = date
    elif period == "last_week":
        date_filter = datetime.now().date() - timedelta(days=7)
    elif period == "last_month":
        date_filter = datetime.now().date() - timedelta(days=30)
    elif period == "last_quarter":
        date_filter = datetime.now().date() - timedelta(days=90)
    
    # Обогащаем данными активности
    result = []
    for student in students:
        # Получаем активности студента
        activities_query = db.query(StudentActivity).filter(
            and_(
                StudentActivity.student_id == student.id,
                StudentActivity.teacher_id == current_user.id
            )
        )
        
        if date:
            # Конкретная дата
            activities_query = activities_query.filter(StudentActivity.lesson_date == date)
        elif date_filter:
            # Период
            activities_query = activities_query.filter(
                StudentActivity.lesson_date >= date_filter
            )
        
        # Сортируем по дате создания
        activities_query = activities_query.order_by(StudentActivity.created_at.desc())
        
        activities_list = activities_query.all()
        
        # Вычисляем статистику
        total_tasks = sum(a.tasks_total for a in activities_list) or 0
        completed_tasks = sum(a.tasks_completed for a in activities_list) or 0
        progress = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
        
        # AI-оценка с объяснением (последняя активность)
        ai_score = None
        ai_explanation = ""
        manual_score = None
        comment = ""
        
        if activities_list:
            latest_activity = activities_list[0]
            ai_score = latest_activity.ai_score
            ai_explanation = latest_activity.ai_explanation or ""
            manual_score = latest_activity.manual_score
            comment = latest_activity.teacher_comment or ""
        
        # Собираем группы (пока пустые, группы добавим позже)
        groups = []
        
        # Определяем активность
        last_active_str = "не активен"
        if student.last_active:
            days_diff = (datetime.now() - student.last_active).days
            if days_diff == 0:
                last_active_str = "сегодня"
            elif days_diff == 1:
                last_active_str = "1 дн. назад"
            else:
                last_active_str = f"{days_diff} дн. назад"
        
        student_data = {
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "grade": student.grade or "Не указан",
            "groups": groups,
            "tasksCompleted": completed_tasks,
            "totalTasks": total_tasks,
            "lastActive": last_active_str,
            "aiScore": ai_score,  # 0-100 баллов
            "aiExplanation": ai_explanation,  # объяснение от ИИ
            "manualScore": manual_score or "",  # оценка преподавателя
            "comment": comment,
            "group": groups[0] if groups else "Без группы"
        }
        
        result.append(student_data)
    
    return result

# Получить группы преподавателя (пока заглушка)
@router.get("/groups")
async def get_groups(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список групп для селектора"""
    
    # Пока возвращаем статические группы
    group_names = ["Все группы", "Математика", "Физика", "Химия"]
    
    return group_names

# Получить темы для конкретного ученика
@router.get("/topics")
async def get_topics(
    student_id: Optional[int] = Query(None),
    group: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить темы уроков для селектора"""
    
    query = db.query(distinct(StudentActivity.topic)).filter(
        and_(
            StudentActivity.teacher_id == current_user.id,
            StudentActivity.topic.isnot(None),
            StudentActivity.topic != ""
        )
    )
    
    # Фильтр по ученику
    if student_id:
        query = query.filter(StudentActivity.student_id == student_id)
    
    topics = query.all()
    return [topic[0] for topic in topics if topic[0]]

# Проверка задания ИИ
async def check_task_with_ai(task_data):
    """Отправляет задание на проверку ИИ и получает оценку с объяснением"""
    
    # Пока заглушка - в будущем здесь будет реальный AI API
    import random
    
    # Имитируем работу ИИ
    score = random.randint(60, 95)
    explanations = [
        "Хорошее понимание темы, но есть небольшие недочеты в оформлении.",
        "Отличная работа! Все задания выполнены правильно.",
        "Правильный подход к решению, но допущена арифметическая ошибка.",
        "Хорошо структурированный ответ, показано понимание материала."
    ]
    
    return {
        "score": score,
        "explanation": random.choice(explanations)
    }

# Ученик отправляет выполненное задание
@router.post("/students/{student_id}/submit-task")
async def submit_task(
    student_id: int,
    task_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Ученик отправляет выполненное задание на проверку ИИ"""
    
    # Проверяем доступ к студенту
    student = db.query(Student).filter(
        and_(
            Student.id == student_id,
            Student.teacher_id == current_user.id,
            Student.student_type == StudentTypeEnum.individual
        )
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    # Отправляем на проверку ИИ
    ai_result = await check_task_with_ai({
        "subject": task_data.get("subject", ""),
        "topic": task_data.get("topic", ""),
        "task_description": task_data.get("task_description", ""),
        "student_answer": task_data.get("student_answer", "")
    })
    
    # Создаем запись об активности
    activity = StudentActivity(
        student_id=student_id,
        teacher_id=current_user.id,
        topic=task_data.get("topic", ""),
        tasks_completed=1,
        tasks_total=1,
        ai_score=ai_result["score"],  # 0-100 от ИИ
        ai_explanation=ai_result["explanation"],  # объяснение ИИ
        lesson_date=task_data.get("lesson_date", date.today())
    )
    
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    # Обновляем время последней активности студента
    student.last_active = datetime.now()
    db.commit()
    
    return {
        "message": "Задание проверено ИИ",
        "ai_score": ai_result["score"],
        "ai_explanation": ai_result["explanation"],
        "activity_id": activity.id
    }

# Получить подробное объяснение AI-оценки
@router.get("/activities/{activity_id}/ai-explanation")
async def get_ai_explanation(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить подробное объяснение AI-оценки для конкретной активности"""
    
    activity = db.query(StudentActivity).filter(
        and_(
            StudentActivity.id == activity_id,
            StudentActivity.teacher_id == current_user.id
        )
    ).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Активность не найдена")
    
    # Получаем студента
    student = db.query(Student).filter(Student.id == activity.student_id).first()
    
    return {
        "activity_id": activity.id,
        "student_name": student.full_name if student else "Неизвестен",
        "topic": activity.topic,
        "ai_score": activity.ai_score,
        "ai_explanation": activity.ai_explanation or "Объяснение отсутствует",
        "manual_score": activity.manual_score,
        "teacher_comment": activity.teacher_comment or "",
        "lesson_date": activity.lesson_date,
        "created_at": activity.created_at
    }

# Принять или скорректировать AI-оценку
@router.put("/activities/{activity_id}/review-ai-score")
async def review_ai_score(
    activity_id: int,
    review_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Преподаватель принимает или корректирует AI-оценку"""
    
    activity = db.query(StudentActivity).filter(
        and_(
            StudentActivity.id == activity_id,
            StudentActivity.teacher_id == current_user.id
        )
    ).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Активность не найдена")
    
    action = review_data.get("action")  # "accept", "modify", "reject"
    
    if action == "accept":
        # Принимаем AI-оценку
        activity.manual_score = activity.ai_score
        activity.teacher_comment = review_data.get("comment", "Согласен с оценкой ИИ")
        
    elif action == "modify":
        # Корректируем оценку
        new_score = review_data.get("manual_score")
        if new_score is not None and 0 <= new_score <= 100:
            activity.manual_score = new_score
            activity.teacher_comment = review_data.get("comment", f"Скорректировано с {activity.ai_score} на {new_score}")
        else:
            raise HTTPException(status_code=400, detail="Некорректная оценка (должна быть 0-100)")
    
    elif action == "reject":
        # Отклоняем AI-оценку, ставим свою
        new_score = review_data.get("manual_score")
        if new_score is not None and 0 <= new_score <= 100:
            activity.manual_score = new_score
            activity.teacher_comment = review_data.get("comment", f"Не согласен с ИИ ({activity.ai_score}), ставлю {new_score}")
        else:
            raise HTTPException(status_code=400, detail="Необходимо указать вашу оценку")
    
    else:
        raise HTTPException(status_code=400, detail="Действие должно быть: accept, modify или reject")
    
    db.commit()
    
    return {
        "message": f"Оценка {action}",
        "ai_score": activity.ai_score,
        "final_score": activity.manual_score,
        "teacher_comment": activity.teacher_comment
    }

# Обновить оценку студента
@router.put("/students/{student_id}/grade")
async def update_student_grade(
    student_id: int,
    grade_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить оценку студента"""
    
    grade = grade_data.get("grade")
    lesson_date = grade_data.get("date", date.today())
    topic = grade_data.get("topic", "")
    
    # Проверяем доступ к студенту
    student = db.query(Student).filter(
        and_(
            Student.id == student_id,
            Student.teacher_id == current_user.id,
            Student.student_type == StudentTypeEnum.individual
        )
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    # Ищем или создаем активность за этот день
    activity = db.query(StudentActivity).filter(
        and_(
            StudentActivity.student_id == student_id,
            StudentActivity.teacher_id == current_user.id,
            StudentActivity.lesson_date == lesson_date
        )
    ).first()
    
    if not activity:
        activity = StudentActivity(
            student_id=student_id,
            teacher_id=current_user.id,
            lesson_date=lesson_date,
            topic=topic
        )
        db.add(activity)
    
    activity.manual_score = int(grade) if grade else None
    if topic:
        activity.topic = topic
    
    db.commit()
    return {"message": "Оценка обновлена"}

# Обновить комментарий студента
@router.put("/students/{student_id}/comment")
async def update_student_comment(
    student_id: int,
    comment_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить комментарий студента"""
    
    comment = comment_data.get("comment", "")
    lesson_date = comment_data.get("date", date.today())
    
    # Проверяем доступ к студенту
    student = db.query(Student).filter(
        and_(
            Student.id == student_id,
            Student.teacher_id == current_user.id,
            Student.student_type == StudentTypeEnum.individual
        )
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    # Ищем или создаем активность
    activity = db.query(StudentActivity).filter(
        and_(
            StudentActivity.student_id == student_id,
            StudentActivity.teacher_id == current_user.id,
            StudentActivity.lesson_date == lesson_date
        )
    ).first()
    
    if not activity:
        activity = StudentActivity(
            student_id=student_id,
            teacher_id=current_user.id,
            lesson_date=lesson_date
        )
        db.add(activity)
    
    activity.teacher_comment = comment
    db.commit()
    return {"message": "Комментарий обновлен"}

# Применить AI-оценки
@router.post("/students/apply-ai-grades")
async def apply_ai_grades(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Применить AI-оценки для выбранных студентов"""
    
    student_ids = request_data.get("student_ids", [])
    lesson_date = request_data.get("date", date.today())
    
    updated_count = 0
    
    for student_id in student_ids:
        # Находим активность с AI-оценкой
        activity = db.query(StudentActivity).filter(
            and_(
                StudentActivity.student_id == student_id,
                StudentActivity.teacher_id == current_user.id,
                StudentActivity.lesson_date == lesson_date,
                StudentActivity.ai_score.isnot(None)
            )
        ).first()
        
        if activity and activity.ai_score:
            activity.manual_score = activity.ai_score
            updated_count += 1
    
    db.commit()
    return {
        "message": f"AI-оценки применены для {updated_count} студентов",
        "updated_count": updated_count
    }

# Сохранить все оценки
@router.post("/students/save-grades")
async def save_grades(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Сохранить все оценки журнала"""
    
    students_data = request_data.get("students", [])
    lesson_date = request_data.get("date", date.today())
    topic = request_data.get("topic", "")
    
    saved_count = 0
    
    for student_data in students_data:
        if student_data.get("manualScore") or student_data.get("comment"):
            activity = db.query(StudentActivity).filter(
                and_(
                    StudentActivity.student_id == student_data["id"],
                    StudentActivity.teacher_id == current_user.id,
                    StudentActivity.lesson_date == lesson_date
                )
            ).first()
            
            if not activity:
                activity = StudentActivity(
                    student_id=student_data["id"],
                    teacher_id=current_user.id,
                    lesson_date=lesson_date,
                    topic=topic
                )
                db.add(activity)
            
            if student_data.get("manualScore"):
                activity.manual_score = int(student_data["manualScore"])
            if student_data.get("comment"):
                activity.teacher_comment = student_data["comment"]
            
            saved_count += 1
    
    db.commit()
    return {
        "message": f"Сохранено записей: {saved_count}",
        "saved_count": saved_count
    }

# Создать записи в журнале из AI-инструментов
@router.post("/ai-tools/create-journal-entries")
async def create_journal_entries_from_ai(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создать записи в журнале на основе сгенерированного AI-контента"""
    
    topic = request_data.get("topic")
    student_ids = request_data.get("student_ids", [])
    generated_content = request_data.get("generated_content", "")
    tool_type = request_data.get("tool_type", "ai_tool")
    lesson_date = request_data.get("lesson_date", date.today())
    
    if not topic:
        raise HTTPException(status_code=400, detail="Тема обязательна")
    
    if not student_ids:
        raise HTTPException(status_code=400, detail="Выберите хотя бы одного студента")
    
    # Проверяем что все студенты принадлежат текущему преподавателю
    students = db.query(Student).filter(
        and_(
            Student.id.in_(student_ids),
            Student.teacher_id == current_user.id,
            Student.student_type == StudentTypeEnum.individual,
            Student.is_active == True
        )
    ).all()
    
    if len(students) != len(student_ids):
        raise HTTPException(status_code=403, detail="Нет доступа к некоторым студентам")
    
    created_count = 0
    
    # Создаем активности для каждого студента
    for student_id in student_ids:
        # Проверяем, нет ли уже записи за эту дату с этой темой
        existing_activity = db.query(StudentActivity).filter(
            and_(
                StudentActivity.student_id == student_id,
                StudentActivity.teacher_id == current_user.id,
                StudentActivity.lesson_date == lesson_date,
                StudentActivity.topic == topic
            )
        ).first()
        
        if existing_activity:
            # Обновляем существующую запись
            existing_activity.activity_type = tool_type
            existing_activity.teacher_comment = f"Обновлено из {tool_type}: {generated_content[:100]}..."
        else:
            # Создаем новую запись
            activity = StudentActivity(
                student_id=student_id,
                teacher_id=current_user.id,
                topic=topic,
                lesson_date=lesson_date,
                activity_type=tool_type,
                tasks_total=1,
                tasks_completed=0,  # Ученик еще не выполнил задание
                teacher_comment=f"Создано из {tool_type}: {generated_content[:100]}..."
            )
            db.add(activity)
            created_count += 1
    
    db.commit()
    
    return {
        "message": f"Тема '{topic}' добавлена в журнал для {len(student_ids)} студентов",
        "created_count": created_count,
        "topic": topic,
        "students_count": len(student_ids)
    }

# Получить активности созданные из AI-инструментов
@router.get("/ai-tools/activities")
async def get_ai_tool_activities(
    tool_type: Optional[str] = Query(None),
    days: int = Query(30, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список активностей созданных из AI-инструментов"""
    
    since_date = datetime.now().date() - timedelta(days=days)
    
    query = db.query(StudentActivity).filter(
        and_(
            StudentActivity.teacher_id == current_user.id,
            StudentActivity.lesson_date >= since_date,
            StudentActivity.activity_type.like('%tool%')  # AI-инструменты содержат 'tool'
        )
    )
    
    if tool_type:
        query = query.filter(StudentActivity.activity_type == tool_type)
    
    activities = query.order_by(StudentActivity.created_at.desc()).all()
    
    # Группируем по темам
    topics_stats = {}
    for activity in activities:
        topic = activity.topic or "Без темы"
        if topic not in topics_stats:
            topics_stats[topic] = {
                "topic": topic,
                "total_students": 0,
                "tool_types": set(),
                "dates": set()
            }
        
        topics_stats[topic]["total_students"] += 1
        topics_stats[topic]["tool_types"].add(activity.activity_type)
        topics_stats[topic]["dates"].add(activity.lesson_date.isoformat())
    
    # Преобразуем в список
    topics_list = []
    for topic_data in topics_stats.values():
        topic_data["tool_types"] = list(topic_data["tool_types"])
        topic_data["dates"] = sorted(list(topic_data["dates"]))
        topics_list.append(topic_data)
    
    return {
        "topics": topics_list,
        "total_activities": len(activities),
        "period_days": days
    }

# Получить статистику использования AI-инструментов
@router.get("/ai-tools/stats")
async def get_ai_tools_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Статистика использования AI-инструментов"""
    
    # Статистика за последние 30 дней
    since_date = datetime.now().date() - timedelta(days=30)
    
    # Подсчет по типам инструментов
    tool_usage = db.query(
        StudentActivity.activity_type,
        func.count(StudentActivity.id).label('count'),
        func.count(distinct(StudentActivity.topic)).label('unique_topics'),
        func.count(distinct(StudentActivity.student_id)).label('unique_students')
    ).filter(
        and_(
            StudentActivity.teacher_id == current_user.id,
            StudentActivity.lesson_date >= since_date,
            StudentActivity.activity_type.like('%tool%')
        )
    ).group_by(StudentActivity.activity_type).all()
    
    tool_stats = []
    for usage in tool_usage:
        tool_name = usage.activity_type.replace('_tool', '').replace('_', ' ').title()
        tool_stats.append({
            "tool_name": tool_name,
            "tool_type": usage.activity_type,
            "usage_count": usage.count,
            "unique_topics": usage.unique_topics,
            "unique_students": usage.unique_students
        })
    
    # Общая статистика
    total_ai_activities = sum(stat["usage_count"] for stat in tool_stats)
    
    return {
        "tool_usage": tool_stats,
        "total_ai_activities": total_ai_activities,
        "period": "last_30_days",
        "most_used_tool": max(tool_stats, key=lambda x: x["usage_count"]) if tool_stats else None
    }

# Удалить тему созданную из AI-инструмента
@router.delete("/ai-tools/topic/{topic}")
async def delete_ai_topic(
    topic: str,
    confirm: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удалить все записи по теме созданной из AI-инструмента"""
    
    if not confirm:
        # Сначала показываем что будет удалено
        activities = db.query(StudentActivity).filter(
            and_(
                StudentActivity.teacher_id == current_user.id,
                StudentActivity.topic == topic,
                StudentActivity.activity_type.like('%tool%')
            )
        ).all()
        
        if not activities:
            raise HTTPException(status_code=404, detail="Тема не найдена")
        
        students_affected = len(set(a.student_id for a in activities))
        
        return {
            "message": "Подтвердите удаление",
            "topic": topic,
            "activities_count": len(activities),
            "students_affected": students_affected,
            "warning": "Это действие нельзя отменить",
            "confirm_url": f"/api/ai-tools/topic/{topic}?confirm=true"
        }
    
    # Удаляем записи
    deleted_count = db.query(StudentActivity).filter(
        and_(
            StudentActivity.teacher_id == current_user.id,
            StudentActivity.topic == topic,
            StudentActivity.activity_type.like('%tool%')
        )
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Удалено {deleted_count} записей по теме '{topic}'",
        "deleted_count": deleted_count
    }

# ========== Student Disciplines/Subjects ==========

@router.get("/disciplines", response_model=dict)
def get_student_disciplines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список предметов для ученика (предметы его класса)
    
    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 15,
                    "subject": "Физика",
                    "grade": 7,
                    "displayName": "Физика - 7 класс",
                    "teacher_count": 2,
                    "file_count": 3,
                    "files": [...]
                }
            ]
        }
    """
    # Получаем информацию об ученике
    student_info = db.query(Student).filter(Student.email == current_user.email).first()
    
    if not student_info or not student_info.grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Информация об ученике не найдена или класс не указан"
        )
    
    # Получаем все дисциплины класса ученика в его школе
    disciplines = (
        db.query(Discipline)
        .filter(
            Discipline.school_id == current_user.school_id,
            Discipline.grade == student_info.grade
        )
        .order_by(Discipline.subject)
        .all()
    )
    
    data = []
    for discipline in disciplines:
        # Получаем учителей
        teacher_count = len(get_discipline_teachers(db, discipline.id, active_only=True))
        
        # Получаем файлы
        files = get_discipline_files(db, discipline.id)
        files_data = []
        for file in files:
            files_data.append({
                "id": file.id,
                "filename": file.filename,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "created_at": file.created_at.isoformat()
            })
        
        discipline_data = {
            "id": discipline.id,
            "subject": discipline.subject,
            "grade": discipline.grade,
            "displayName": f"{discipline.subject} - {discipline.grade} класс",
            "teacher_count": teacher_count,
            "file_count": len(files),
            "files": files_data
        }
        data.append(discipline_data)
    
    logger.info(f"Student {current_user.id} fetched {len(data)} disciplines for grade {student_info.grade}")
    
    return {
        "success": True,
        "data": data
    }
