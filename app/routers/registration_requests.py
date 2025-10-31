from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from app.schemas.registration_request import (
    RegistrationRequestCreate,
    IndependentRegistrationRequest,
    RegistrationRequestOut,
    IndependentRegistrationResponse
)
from app.models.registration_request import RegistrationRequest
from app.models.school import School
from app.models.user import User
from app.auth.hashing import get_password_hash
from app.auth.jwt_handler import create_access_token

router = APIRouter(tags=["Registration Requests"])

def handle_registration(request_data: RegistrationRequestCreate, db: Session):
    """Общая логика регистрации"""
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

# Множественные endpoint'ы для совместимости с разными URL на фронтенде
@router.post("/register", response_model=RegistrationRequestOut)
def create_registration_v1(request_data: RegistrationRequestCreate, db: Session = Depends(get_db)):
    """POST /register"""
    return handle_registration(request_data, db)

@router.post("/registration", response_model=RegistrationRequestOut)
def create_registration_v2(request_data: RegistrationRequestCreate, db: Session = Depends(get_db)):
    """POST /registration"""
    return handle_registration(request_data, db)

@router.post("/registration/register", response_model=RegistrationRequestOut)
def create_registration_v3(request_data: RegistrationRequestCreate, db: Session = Depends(get_db)):
    """POST /registration/register"""
    return handle_registration(request_data, db)

@router.post("/register-request", response_model=RegistrationRequestOut)
def create_registration_v4(request_data: RegistrationRequestCreate, db: Session = Depends(get_db)):
    """POST /register-request (старый URL для совместимости)"""
    return handle_registration(request_data, db)

@router.post("/register-request/", response_model=RegistrationRequestOut)
def create_registration_v5(request_data: RegistrationRequestCreate, db: Session = Depends(get_db)):
    """POST /register-request/ (старый URL с trailing slash)"""
    return handle_registration(request_data, db)

@router.post("/register-request/independent", response_model=IndependentRegistrationResponse)
def create_independent_registration(request_data: IndependentRegistrationRequest, db: Session = Depends(get_db)):
    """POST /register-request/independent - самостоятельная регистрация БЕЗ привязки к школе

    Независимые пользователи:
    - НЕ связаны ни с какой школой (school_id = NULL)
    - Создаются СРАЗУ без ожидания одобрения
    - Получают токен для автоматического входа
    - Сразу переходят на главную страницу

    Отличие от школьной регистрации:
    - Школьная: Создаёт заявку → Ждёт одобрения админа → Админ создаёт пользователя
    - Независимая: Сразу создаёт пользователя → Автоматический вход
    """

    # Проверка на дубликат email
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    # Хешируем пароль
    hashed_password = get_password_hash(request_data.password)

    # Создаём пользователя НАПРЯМУЮ (без заявки и одобрения)
    new_user = User(
        full_name=request_data.full_name,
        email=request_data.email,
        hashed_password=hashed_password,
        role=request_data.role,
        school_id=None  # Независимые НЕ связаны со школой
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Создаём токен для автоматического входа
    access_token = create_access_token(data={
        "sub": new_user.email,
        "user_id": new_user.id,
        "role": new_user.role
    })

    # Возвращаем токен и данные пользователя
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "school_id": new_user.school_id
        }
    }
