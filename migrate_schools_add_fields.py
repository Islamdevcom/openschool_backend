"""
Migration: Add address, max_users, and created_at fields to schools table

Добавляет в таблицу schools:
- address VARCHAR(500) NULL - адрес школы
- max_users INTEGER DEFAULT 500 NOT NULL - максимум пользователей
- created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP - дата создания

Запуск: python migrate_schools_add_fields.py
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def migrate():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ ERROR: DATABASE_URL не найден в переменных окружения")
        return

    print(f"🔗 Подключение к базе данных...")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        print("\n📋 Начинаем миграцию таблицы schools...")

        # Проверяем существует ли таблица schools
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'schools'
            );
        """))

        if not result.scalar():
            print("❌ Таблица schools не существует!")
            return

        print("✅ Таблица schools найдена")

        # Проверяем какие колонки уже существуют
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'schools';
        """))

        existing_columns = {row[0] for row in result}
        print(f"📊 Существующие колонки: {existing_columns}")

        # Добавляем address если не существует
        if 'address' not in existing_columns:
            print("➕ Добавляем колонку address...")
            conn.execute(text("""
                ALTER TABLE schools
                ADD COLUMN address VARCHAR(500);
            """))
            print("✅ Колонка address добавлена")
        else:
            print("⏭️  Колонка address уже существует")

        # Добавляем max_users если не существует
        if 'max_users' not in existing_columns:
            print("➕ Добавляем колонку max_users...")
            conn.execute(text("""
                ALTER TABLE schools
                ADD COLUMN max_users INTEGER DEFAULT 500 NOT NULL;
            """))
            print("✅ Колонка max_users добавлена")
        else:
            print("⏭️  Колонка max_users уже существует")

        # Добавляем created_at если не существует
        if 'created_at' not in existing_columns:
            print("➕ Добавляем колонку created_at...")
            conn.execute(text("""
                ALTER TABLE schools
                ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            """))
            print("✅ Колонка created_at добавлена")
        else:
            print("⏭️  Колонка created_at уже существует")

        # Обновляем существующие записи без max_users
        print("🔄 Проверяем существующие записи...")
        result = conn.execute(text("""
            SELECT COUNT(*) FROM schools WHERE max_users IS NULL;
        """))
        null_count = result.scalar()

        if null_count > 0:
            print(f"🔄 Обновляем {null_count} записей с NULL max_users...")
            conn.execute(text("""
                UPDATE schools
                SET max_users = 500
                WHERE max_users IS NULL;
            """))
            print(f"✅ Обновлено {null_count} записей")

        conn.commit()

        # Проверяем финальную структуру
        print("\n📊 Финальная структура таблицы schools:")
        result = conn.execute(text("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'schools'
            ORDER BY ordinal_position;
        """))

        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            default = f"DEFAULT {row[3]}" if row[3] else ""
            print(f"  - {row[0]}: {row[1]} {nullable} {default}")

        print("\n✅ Миграция завершена успешно!")

if __name__ == "__main__":
    print("=" * 60)
    print("  MIGRATION: Add fields to schools table")
    print("=" * 60)

    try:
        migrate()
    except Exception as e:
        print(f"\n❌ ОШИБКА при миграции: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 60)
