from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging

from app.routers import (
    auth,
    users,
    lectures,
    tasks,
    chat,
    dashboard,
    schools,
    registration_requests,
    invites,
    student,
)

from app.database import SessionLocal
from app.models.user import User, RoleEnum
from app.models.school import School
from app.auth.hashing import get_password_hash
from app.routers.student import router as students_router

# Настройка логгера
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenSchool AI",
        version="1.0.0",
        description="AI-помощник для студентов и преподавателей"
    )

    # CORS настройки - получаем разрешенные origins из переменной окружения или используем дефолтные
    allowed_origins_str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,https://openschool-frontend.vercel.app"
    )
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

    print(f"🔒 CORS настройки: разрешенные origins = {allowed_origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # Explicit список origins для работы с credentials
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Обработчик для всех необработанных исключений - гарантирует CORS заголовки даже при ошибках
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Необработанное исключение: {type(exc).__name__}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Внутренняя ошибка сервера: {str(exc)}"},
        )

    # Подключаем роутеры
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(users.router)
    app.include_router(lectures.router, prefix="/lectures", tags=["Lectures"])
    app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
    app.include_router(chat.router, prefix="/chat", tags=["Chat"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
    app.include_router(schools.router, prefix="/schools", tags=["Schools"])
    app.include_router(registration_requests.router)
    app.include_router(invites.router)
    app.include_router(students_router, tags=["Students"])

    @app.on_event("startup")
    def create_test_data():
        db = SessionLocal()
        school = db.query(School).filter(School.name == "OpenSchool Test School").first()
        if not school:
            school = School(name="OpenSchool Test School", code="SCHO125")
            db.add(school)
            db.commit()
            db.refresh(school)
            print(f"✅ Создана школа: {school.name} (код: {school.code})")

        teacher = db.query(User).filter(User.email == "teacher@example.com").first()
        if not teacher:
            db.add(User(
                full_name="Test Teacher",
                email="teacher@example.com",
                hashed_password=get_password_hash("1234"),
                role=RoleEnum.teacher,
                school_id=school.id
            ))

        student = db.query(User).filter(User.email == "student@example.com").first()
        if not student:
            db.add(User(
                full_name="Test Student",
                email="student@example.com",
                hashed_password=get_password_hash("1234"),
                role=RoleEnum.student,
                school_id=school.id
            ))

        db.commit()
        db.close()

    return app

app = create_app()
