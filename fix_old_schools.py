"""
Быстрое исправление: обновить старые записи школ
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL не найден")
    exit(1)

print("🔧 Исправляем старые записи школ...")

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    # Обновляем max_users для всех записей где NULL
    result = conn.execute(text('''
        UPDATE schools
        SET max_users = 500
        WHERE max_users IS NULL;
    '''))

    print(f'✅ Обновлено max_users для {result.rowcount} школ')

    conn.commit()

    # Проверяем все школы
    result = conn.execute(text('SELECT id, name, code, address, max_users FROM schools ORDER BY id;'))
    print('\n📊 Все школы в базе:')
    for row in result:
        address = row[3] if row[3] else '(нет адреса)'
        print(f'  ID {row[0]}: {row[1]}')
        print(f'    Code: {row[2]}')
        print(f'    Address: {address}')
        print(f'    Max users: {row[4]}')
        print()

print("✅ Готово!")
