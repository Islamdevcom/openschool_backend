from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
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
    teacher,
    admin,
    init,
)

from app.database import SessionLocal
from app.models.user import User, RoleEnum
from app.models.school import School
from app.auth.hashing import get_password_hash
from app.routers.student import router as students_router

# Настройка логгера
logger = logging.getLogger(__name__)


# Custom middleware для CORS - добавляет заголовки ДО любой обработки
class CustomCORSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_origins):
        super().__init__(app)
        self.allowed_origins = allowed_origins

    async def dispatch(self, request: Request, call_next):
        # Получаем origin из запроса
        origin = request.headers.get("origin")

        # Обрабатываем preflight OPTIONS запросы
        if request.method == "OPTIONS":
            response = JSONResponse(content={}, status_code=200)
        else:
            try:
                response = await call_next(request)
            except Exception as e:
                logger.error(f"Ошибка в обработке запроса: {str(e)}", exc_info=True)
                response = JSONResponse(
                    status_code=500,
                    content={"detail": f"Internal server error: {str(e)}"}
                )

        # ВСЕГДА добавляем CORS заголовки
        if origin and (origin in self.allowed_origins or "*" in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Expose-Headers"] = "*"

        return response

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

    logger.info(f"🔒 CORS настройки: разрешенные origins = {allowed_origins}")

    # Используем custom CORS middleware для гарантированной работы CORS
    app.add_middleware(CustomCORSMiddleware, allowed_origins=allowed_origins)

    # Подключаем роутеры
    app.include_router(init.router, tags=["Initialization"])
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
    app.include_router(teacher.router, prefix="/api", tags=["Teacher"])
    app.include_router(admin.router, prefix="/api", tags=["Admin"])

    @app.on_event("startup")
    def create_test_data():
        """
        Создание тестовых данных ТОЛЬКО для локальной разработки.

        В продакшене (Railway) эта функция НЕ выполняется для безопасности.
        Установите ENVIRONMENT=development для активации.
        """
        # Проверяем режим окружения
        environment = os.getenv("ENVIRONMENT", "production").lower()

        if environment != "development":
            logger.info("🔒 Production mode: skipping test data creation")
            return

        logger.info("🧪 Development mode: creating test data...")

        db = SessionLocal()
        school = db.query(School).filter(School.name == "OpenSchool Test School").first()
        if not school:
            school = School(name="OpenSchool Test School", code="SCHO125")
            db.add(school)
            db.commit()
            db.refresh(school)
            print(f"✅ Создана тестовая школа: {school.name} (код: {school.code})")

        teacher = db.query(User).filter(User.email == "teacher@example.com").first()
        if not teacher:
            db.add(User(
                full_name="Test Teacher",
                email="teacher@example.com",
                hashed_password=get_password_hash("1234"),
                role=RoleEnum.teacher,
                school_id=school.id
            ))
            print(f"✅ Создан тестовый учитель: teacher@example.com")

        student = db.query(User).filter(User.email == "student@example.com").first()
        if not student:
            db.add(User(
                full_name="Test Student",
                email="student@example.com",
                hashed_password=get_password_hash("1234"),
                role=RoleEnum.student,
                school_id=school.id
            ))
            print(f"✅ Создан тестовый студент: student@example.com")

        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            db.add(User(
                full_name="Test School Admin",
                email="admin@example.com",
                hashed_password=get_password_hash("1234"),
                role=RoleEnum.school_admin,
                school_id=school.id
            ))
            print(f"✅ Создан тестовый администратор: admin@example.com")

        superadmin = db.query(User).filter(User.email == "superadmin@example.com").first()
        if not superadmin:
            db.add(User(
                full_name="Super Administrator",
                email="superadmin@example.com",
                hashed_password=get_password_hash("1234"),
                role=RoleEnum.superadmin,
                school_id=None  # Суперадмин не привязан к школе
            ))
            print(f"✅ Создан тестовый суперадмин: superadmin@example.com")

        db.commit()
        db.close()
        print("✅ Все тестовые данные созданы (пароль для всех: 1234)")

    return app

app = create_app()
