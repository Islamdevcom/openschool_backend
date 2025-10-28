from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, RoleEnum
from app.models.teacher_student_relation import TeacherStudentRelation

router = APIRouter(prefix="/api", tags=["users"])

@router.get("/students")
async def get_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список студентов для учителя"""
    
    # Только для учителей
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=403, detail="Доступ только для учителей")
    
    students = []
    
    # Для школьного учителя - все студенты школы
    if current_user.school_id:
        students = db.query(User).filter(
            and_(
                User.role == RoleEnum.student,
                User.school_id == current_user.school_id
            )
        ).all()
    
    # Для независимого учителя - студенты из teacher_student_relations
    else:
        relations = db.query(TeacherStudentRelation).filter(
            TeacherStudentRelation.teacher_id == current_user.id
        ).all()
        
        student_ids = [r.student_id for r in relations]
        if student_ids:
            students = db.query(User).filter(User.id.in_(student_ids)).all()
    
    # Формируем ответ
    result = []
    for student in students:
        result.append({
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "grade": "Не указан",
            "groups": [],
            "tasksCompleted": 0,
            "totalTasks": 0,
            "lastActive": "недавно",
            "aiScore": None,
            "aiExplanation": "",
            "manualScore": "",
            "comment": "",
            "group": "Без группы"
        })
    
    return result