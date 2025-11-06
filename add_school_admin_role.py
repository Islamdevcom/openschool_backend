"""
Добавить роль school_admin в enum базы данных
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL не найден")
    exit(1)

print("🔧 Добавляем роль school_admin в enum...")

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    # Добавляем school_admin в enum если его нет
    try:
        conn.execute(text("""
            ALTER TYPE roleenum ADD VALUE 'school_admin';
        """))
        conn.commit()
        print('✅ Добавлена роль school_admin в enum')
    except Exception as e:
        if 'already exists' in str(e):
            print('✅ Роль school_admin уже существует')
        else:
            print(f'❌ Ошибка: {e}')

    # Проверяем все значения enum
    result = conn.execute(text("""
        SELECT e.enumlabel
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'roleenum'
        ORDER BY e.enumsortorder;
    """))

    print('\n📋 Доступные роли в базе:')
    for row in result:
        print(f'  - {row[0]}')

print('\n✅ Готово!')
