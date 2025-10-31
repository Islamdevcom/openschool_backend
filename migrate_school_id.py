#!/usr/bin/env python3
"""
Безопасная миграция для изменения school_id в nullable.
Запускается при каждом деплое, безопасна для повторного запуска.
"""
import os
import sys
from sqlalchemy import create_engine, text

def migrate_school_id():
    """Делает school_id nullable в таблице register_requests"""
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
                print("ℹ️  Table register_requests doesn't exist yet")
                return

            # Проверяем nullable статус
            result = conn.execute(text("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'register_requests'
                AND column_name = 'school_id';
            """))
            is_nullable = result.scalar()

            if is_nullable == 'NO':
                # Делаем school_id nullable
                conn.execute(text("""
                    ALTER TABLE register_requests
                    ALTER COLUMN school_id DROP NOT NULL;
                """))
                conn.commit()
                print("✅ Successfully made school_id nullable in register_requests")
            else:
                print("ℹ️  school_id is already nullable")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_school_id()
