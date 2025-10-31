#!/usr/bin/env python3
"""
Безопасная миграция для таблицы register_requests.
- Создаёт таблицу если её нет
- Делает school_id nullable если таблица уже существует
"""
import os
import sys
from sqlalchemy import create_engine, text

def migrate_register_requests():
    """Создаёт или обновляет таблицу register_requests"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("⚠️  DATABASE_URL not set, skipping migration")
        return

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
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

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    migrate_register_requests()

