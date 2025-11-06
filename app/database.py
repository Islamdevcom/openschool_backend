from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os

# Для дебага - выведем все переменные окружения
print("=== ENVIRONMENT VARIABLES DEBUG ===")
print(f"DATABASE_URL value: {repr(os.environ.get('DATABASE_URL'))}")
print(f"All env keys: {list(os.environ.keys())}")

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("WARNING: DATABASE_URL is not set, using SQLite")
    DATABASE_URL = "sqlite:///./test.db"

print(f"Using DATABASE_URL: {DATABASE_URL[:50]}...")

# Настройки для PostgreSQL (Neon) с SSL
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Проверять соединение перед использованием
        pool_recycle=3600,   # Обновлять соединения каждый час
        pool_size=10,        # Размер пула соединений
        max_overflow=20,     # Максимум дополнительных соединений
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )
    print("✅ PostgreSQL connection pool configured with SSL support")
else:
    # Для SQLite (разработка)
    engine = create_engine(DATABASE_URL)
    print("✅ SQLite engine created")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
