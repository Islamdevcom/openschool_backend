from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token

router = APIRouter()


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    # Найти пользователя по email
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный email или пароль"
        )

    # Проверка пароля
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный email или пароль"
        )

    # ✅ Генерация токена по user.id (а не email!)
    token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
        "school_id": user.school_id
    }
