from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import List

from app.database import get_db
from app.models.user import User, RoleEnum
from app.models.parent_child import ParentChild
from app.models.student_stats import StudentStats
from app.models.student import Student
from app.models.teacher_discipline import TeacherDiscipline
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/parent", tags=["Parents"])


def verify_parent_child_access(
    parent: User,
    child_id: int,
    db: Session
) -> ParentChild:
    """
    Проверяет, что текущий родитель имеет доступ к ребенку
    """
    if parent.role != RoleEnum.parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуется роль родителя"
        )

    # Проверяем, что ребенок привязан к этому родителю
    link = db.query(ParentChild).filter(
        ParentChild.parent_user_id == parent.id,
        ParentChild.student_user_id == child_id
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ребенок не привязан к вам"
        )

    return link


@router.get("/children")
def get_children(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить список детей текущего родителя с актуальными данными
    """
    if current_user.role != RoleEnum.parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуется роль родителя"
        )

    # Получаем связи с детьми
    parent_links = db.query(ParentChild).filter(
        ParentChild.parent_user_id == current_user.id
    ).all()

    if not parent_links:
        return {"children": []}

    # Получаем данные о детях
    children_data = []
    for link in parent_links:
        # Получаем студента
        student = db.query(User).filter(User.id == link.student_user_id).first()
        if not student:
            continue

        # Получаем статистику студента
        stats = db.query(StudentStats).filter(
            StudentStats.student_user_id == student.id
        ).first()

        # Получаем информацию о классе из таблицы students
        student_info = db.query(Student).filter(Student.email == student.email).first()

        # Генерируем аватар из инициалов
        name_parts = student.full_name.split()
        avatar = "".join([part[0].upper() for part in name_parts[:2]])

        child_data = {
            "id": student.id,
            "name": student.full_name,
            "grade": student_info.grade if student_info else None,
            "avatar": avatar,
            "avgGrade": float(stats.avg_grade) if stats and stats.avg_grade else 0.0,
            "attendance": float(stats.attendance) if stats and stats.attendance else 0.0,
            "warnings": stats.warnings if stats else 0,
            "behavior": float(stats.behavior) if stats and stats.behavior else 0.0
        }
        children_data.append(child_data)

    return {"children": children_data}


@router.get("/child/{child_id}/teachers")
def get_child_teachers(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить список учителей ребенка
    """
    # Проверяем доступ родителя к ребенку
    verify_parent_child_access(current_user, child_id, db)

    # Получаем учителей, которые ведут дисциплины в школе
    # Это упрощенная версия - в реальности нужно получить учителей конкретного класса
    student = db.query(User).filter(User.id == child_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Получаем всех учителей школы
    teachers = db.query(User).filter(
        User.school_id == student.school_id,
        User.role == RoleEnum.teacher
    ).all()

    teachers_data = []
    for teacher in teachers:
        # Получаем дисциплины учителя
        disciplines = db.query(TeacherDiscipline).filter(
            TeacherDiscipline.teacher_id == teacher.id
        ).all()

        subject = ", ".join([d.discipline.name for d in disciplines if d.discipline]) if disciplines else "Не указано"

        teacher_data = {
            "id": teacher.id,
            "name": teacher.full_name,
            "subject": subject,
            "phone": "+7 (777) 123-45-67",  # Заглушка - нужно добавить поле в модель
            "email": teacher.email
        }
        teachers_data.append(teacher_data)

    return {"teachers": teachers_data}


@router.get("/child/{child_id}/grades")
def get_child_grades(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить оценки ребенка

    TODO: Реализовать получение реальных оценок из базы данных
    Требуется создать таблицу grades
    """
    # Проверяем доступ родителя к ребенку
    verify_parent_child_access(current_user, child_id, db)

    # Пока возвращаем заглушку
    # В реальности нужно получить оценки из таблицы grades
    grades_data = [
        {
            "subject": "Математика",
            "grade": 4,
            "date": "2025-11-10",
            "type": "Контрольная работа",
            "teacher": "Петрова А.И."
        },
        {
            "subject": "Русский язык",
            "grade": 5,
            "date": "2025-11-09",
            "type": "Диктант",
            "teacher": "Иванова М.С."
        }
    ]

    return {"grades": grades_data}


@router.get("/child/{child_id}/attendance")
def get_child_attendance(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить посещаемость ребенка

    TODO: Реализовать получение реальной посещаемости из базы данных
    Требуется создать таблицу attendance
    """
    # Проверяем доступ родителя к ребенку
    verify_parent_child_access(current_user, child_id, db)

    # Пока возвращаем заглушку
    attendance_data = {
        "total_days": 100,
        "present_days": 95,
        "absent_days": 5,
        "attendance_percentage": 95.0,
        "recent_absences": [
            {"date": "2025-11-05", "reason": "Болезнь"},
            {"date": "2025-11-01", "reason": "Семейные обстоятельства"}
        ]
    }

    return attendance_data


@router.get("/child/{child_id}/behavior")
def get_child_behavior(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить замечания и похвалы ребенка

    TODO: Реализовать получение реальных замечаний из базы данных
    Требуется создать таблицу behavior_notes
    """
    # Проверяем доступ родителя к ребенку
    verify_parent_child_access(current_user, child_id, db)

    # Получаем статистику поведения
    stats = db.query(StudentStats).filter(
        StudentStats.student_user_id == child_id
    ).first()

    # Пока возвращаем заглушку для истории замечаний
    behavior_data = {
        "behavior_score": float(stats.behavior) if stats and stats.behavior else 0.0,
        "total_warnings": stats.warnings if stats else 0,
        "warnings": [
            {
                "date": "2025-11-08",
                "type": "warning",
                "description": "Опоздание на урок",
                "teacher": "Петрова А.И."
            },
            {
                "date": "2025-11-05",
                "type": "warning",
                "description": "Не выполнено домашнее задание",
                "teacher": "Иванова М.С."
            }
        ],
        "praises": [
            {
                "date": "2025-11-07",
                "type": "praise",
                "description": "Отличная работа на уроке",
                "teacher": "Петрова А.И."
            }
        ]
    }

    return behavior_data


@router.get("/chat/history/{child_id}")
def get_chat_history(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    История чата родителя об этом ребенке

    TODO: Реализовать получение истории чата из базы данных
    Требуется интеграция с таблицей chat
    """
    # Проверяем доступ родителя к ребенку
    verify_parent_child_access(current_user, child_id, db)

    # Пока возвращаем заглушку
    chat_history = {
        "messages": [
            {
                "id": 1,
                "sender": "parent",
                "text": "Как дела у моего ребенка?",
                "timestamp": "2025-11-10T10:00:00Z"
            },
            {
                "id": 2,
                "sender": "teacher",
                "text": "Все хорошо, успеваемость улучшилась!",
                "timestamp": "2025-11-10T10:05:00Z"
            }
        ]
    }

    return chat_history
