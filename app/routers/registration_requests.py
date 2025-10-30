from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from app.schemas.registration_request import RegistrationRequestCreate, RegistrationRequestOut
from app.models.registration_request import RegistrationRequest
from app.models.school import School
from app.models.user import User
from app.auth.hashing import get_password_hash

router = APIRouter(prefix="/registration", tags=["Registration Requests"])

@router.post("/register", response_model=RegistrationRequestOut)
def create_registration_request(request_data: RegistrationRequestCreate, db: Session = Depends(get_db)):
    # Проверка существования школы
    school = db.query(School).filter(School.id == request_data.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Школа не найдена")

    # Проверка на дубликат email в пользователях
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    # Проверка на дубликат email в заявках
    existing_request = db.query(RegistrationRequest).filter(RegistrationRequest.email == request_data.email).first()
    if existing_request:
        raise HTTPException(status_code=400, detail="Заявка с таким email уже существует")

    # Хешируем пароль перед сохранением
    hashed_password = get_password_hash(request_data.password)

    new_request = RegistrationRequest(
        full_name=request_data.full_name,
        email=request_data.email,
        password=hashed_password,  # Сохраняем хешированный пароль
        role=request_data.role,
        school_id=request_data.school_id
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request
