#!/usr/bin/env python3
"""
Безопасная миграция для таблиц:
- register_requests и invite_codes
- disciplines и teacher_disciplines
Создаёт таблицы если их нет
"""
import os
import sys
from sqlalchemy import create_engine, text

def migrate_tables():
    """Создаёт или обновляет таблицы register_requests и invite_codes"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("⚠️  DATABASE_URL not set, skipping migration")
        return

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # ========== Миграция таблицы register_requests ==========
            # Проверяем существование таблицы
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'register_requests'
                );
            """))
            table_exists = result.scalar()

            if not table_exists:
                # Таблица не существует - создаём с правильной структурой
                print("📝 Creating register_requests table...")
                conn.execute(text("""
                    CREATE TABLE register_requests (
                        id SERIAL PRIMARY KEY,
                        full_name VARCHAR NOT NULL,
                        email VARCHAR UNIQUE NOT NULL,
                        password VARCHAR NOT NULL,
                        role VARCHAR NOT NULL,
                        status VARCHAR DEFAULT 'pending',
                        school_id INTEGER REFERENCES schools(id) NULL
                    );
                """))
                conn.commit()
                print("✅ Successfully created register_requests table with nullable school_id")
                return

            # Таблица существует - проверяем nullable статус school_id
            result = conn.execute(text("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'register_requests'
                AND column_name = 'school_id';
            """))
            is_nullable = result.scalar()

            if is_nullable == 'NO':
                # Делаем school_id nullable
                print("📝 Making school_id nullable...")
                conn.execute(text("""
                    ALTER TABLE register_requests
                    ALTER COLUMN school_id DROP NOT NULL;
                """))
                conn.commit()
                print("✅ Successfully made school_id nullable in register_requests")
            else:
                print("ℹ️  register_requests table already exists with nullable school_id")

            # ========== Миграция таблицы invite_codes ==========
            # Проверяем существование таблицы invite_codes
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'invite_codes'
                );
            """))
            invite_codes_exists = result.scalar()

            if not invite_codes_exists:
                # Таблица не существует - создаём
                print("📝 Creating invite_codes table...")
                conn.execute(text("""
                    CREATE TABLE invite_codes (
                        id SERIAL PRIMARY KEY,
                        code VARCHAR UNIQUE NOT NULL,
                        teacher_id INTEGER REFERENCES users(id) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        used BOOLEAN DEFAULT FALSE
                    );
                    CREATE INDEX idx_invite_codes_code ON invite_codes(code);
                    CREATE INDEX idx_invite_codes_teacher_id ON invite_codes(teacher_id);
                """))
                conn.commit()
                print("✅ Successfully created invite_codes table")
            else:
                print("ℹ️  invite_codes table already exists")

            # ========== Миграция таблицы disciplines ==========
            # Проверяем существование таблицы disciplines
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'disciplines'
                );
            """))
            disciplines_exists = result.scalar()

            if not disciplines_exists:
                # Таблица не существует - создаём
                print("📝 Creating disciplines table...")
                conn.execute(text("""
                    CREATE TABLE disciplines (
                        id SERIAL PRIMARY KEY,
                        school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
                        subject VARCHAR(100) NOT NULL,
                        grade INTEGER NOT NULL CHECK (grade >= 1 AND grade <= 11),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(school_id, subject, grade)
                    );
                    CREATE INDEX idx_disciplines_school ON disciplines(school_id);
                """))
                conn.commit()
                print("✅ Successfully created disciplines table")
            else:
                print("ℹ️  disciplines table already exists")

            # ========== Миграция таблицы teacher_disciplines ==========
            # Проверяем существование таблицы teacher_disciplines
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'teacher_disciplines'
                );
            """))
            teacher_disciplines_exists = result.scalar()

            if not teacher_disciplines_exists:
                # Таблица не существует - создаём
                print("📝 Creating teacher_disciplines table...")
                conn.execute(text("""
                    CREATE TABLE teacher_disciplines (
                        id SERIAL PRIMARY KEY,
                        teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        discipline_id INTEGER NOT NULL REFERENCES disciplines(id) ON DELETE CASCADE,
                        assigned_by INTEGER NOT NULL REFERENCES users(id),
                        assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        UNIQUE(teacher_id, discipline_id)
                    );
                    CREATE INDEX idx_teacher_disciplines_teacher ON teacher_disciplines(teacher_id);
                    CREATE INDEX idx_teacher_disciplines_discipline ON teacher_disciplines(discipline_id);
                """))
                conn.commit()
                print("✅ Successfully created teacher_disciplines table")
            else:
                print("ℹ️  teacher_disciplines table already exists")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    migrate_tables()

