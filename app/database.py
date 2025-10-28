from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
