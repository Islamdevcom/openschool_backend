from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenSchool AI",
        version="1.0.0",
        description="AI-помощник для студентов и преподавателей"
    )

    # CORS настройки - добавляем только один раз
    app.add_middleware(
    CORSMiddleware,
        allow_origins=["*"],  # временно разрешаем все
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем роутеры
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(users.router)
    app.include_router(lectures.router, prefix="/lectures", tags=["Lectures"])
    app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
    app.include_router(chat.router, prefix="/chat", tags=["Chat"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
    app.include_router(schools.router, prefix="/schools", tags=["Schools"])
    app.include_router(registration_requests.router, prefix="/registration", tags=["Registration"])
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
