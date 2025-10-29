from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.invite_code import InviteCode                   
from ..models.teacher_student_relation import TeacherStudentRelation  # ✅ ИСПРАВЛЕНО
from ..crud.invite_code import (                               
    create_invite_code as create_invite,
    use_invite_code as use_invite,
)
from .. import schemas

router = APIRouter(prefix="/invites", tags=["invites"])


def ensure_teacher(u: User):
    if u.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create/list/delete invites")


def ensure_student(u: User):
    if u.role != "student":
        raise HTTPException(status_code=403, detail="Only students can use invites")


# ---------- Schemas ----------
class CodeRequest(BaseModel):
    code: str


# ---------- Endpoints ----------
@router.post("/create", response_model=schemas.InviteCodeResponse)
def create_invite_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_teacher(current_user)
    invite = create_invite(db, current_user.id)
    return invite


@router.post("/use")
def use_invite_code_endpoint(
    data: CodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_student(current_user)
    status = use_invite(db, data.code, current_user.id)

    if status == "expired":
        raise HTTPException(status_code=400, detail="Invite code expired")
    if status == "student_not_found":
        raise HTTPException(status_code=404, detail="Student not found")
    if status == "invalid":
        raise HTTPException(status_code=404, detail="Invalid or used code")
    if status == "already_linked":
        raise HTTPException(status_code=400, detail="Already connected to this teacher")
    if status == "success":
        return {"message": "Successfully connected to teacher"}

    raise HTTPException(status_code=400, detail=f"Unknown status: {status}")


@router.get("/mine")
def my_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_teacher(current_user)
    invites = (
        db.query(InviteCode)
        .filter(InviteCode.teacher_id == current_user.id)
        .order_by(InviteCode.id.desc())
        .all()
    )
    return [
        {"id": i.id, "code": i.code, "created_at": i.created_at, "used": i.used}
        for i in invites
    ]


@router.get("/debug/{code}")
def debug_code(code: str, db: Session = Depends(get_db)):
    """Временный endpoint для отладки - показывает информацию о коде"""
    invite = db.query(InviteCode).filter(InviteCode.code == code).first()
    if invite:
        return {
            "exists": True,
            "code": invite.code,
            "used": invite.used,
            "teacher_id": invite.teacher_id,
            "created_at": str(invite.created_at)
        }
    return {"exists": False, "message": "Code not found"}


@router.get("/debug-user")
def debug_current_user(current_user: User = Depends(get_current_user)):
    """Показывает информацию о текущем пользователе"""
    return {
        "id": current_user.id,
        "role": current_user.role,
        "full_name": getattr(current_user, 'full_name', 'no full_name field'),
        "email": getattr(current_user, 'email', 'no email field')
    }


@router.get("/students")
def get_my_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список студентов, привязанных к преподавателю"""
    ensure_teacher(current_user)
    
    # Получаем студентов через связи
    students = (
        db.query(User)
        .join(TeacherStudentRelation, User.id == TeacherStudentRelation.student_id)  # ✅ ИСПРАВЛЕНО
        .filter(TeacherStudentRelation.teacher_id == current_user.id)  # ✅ ИСПРАВЛЕНО
        .all()
    )
    
    return [
        {
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "role": student.role,
            "linked_at": "недавно"
        }
        for student in students
    ]


@router.get("/my-teachers")
def get_my_teachers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список преподавателей, к которым привязан студент"""
    ensure_student(current_user)
    
    teachers = (
        db.query(User)
        .join(TeacherStudentRelation, User.id == TeacherStudentRelation.teacher_id)  # ✅ ИСПРАВЛЕНО
        .filter(TeacherStudentRelation.student_id == current_user.id)  # ✅ ИСПРАВЛЕНО
        .all()
    )
    
    return [
        {
            "id": teacher.id,
            "name": teacher.full_name,
            "email": teacher.email,
            "subject": "Не указан"
        }
        for teacher in teachers
    ]