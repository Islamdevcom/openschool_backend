"""safe_make_school_id_nullable

Revision ID: a31f93a2ae23
Revises: 45891bdce775
Create Date: 2025-10-31 05:09:41.109033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a31f93a2ae23'
down_revision: Union[str, Sequence[str], None] = '45891bdce775'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - safely make school_id nullable."""
    # Используем raw SQL для безопасного изменения
    # Проверяем существование таблицы и колонки перед изменением
    conn = op.get_bind()

    # Проверяем, существует ли таблица register_requests
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'register_requests'
        );
    """))
    table_exists = result.scalar()

    if table_exists:
        # Таблица существует, проверяем nullable статус school_id
        result = conn.execute(sa.text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'register_requests'
            AND column_name = 'school_id';
        """))
        is_nullable = result.scalar()

        # Если колонка НЕ nullable, делаем её nullable
        if is_nullable == 'NO':
            conn.execute(sa.text("""
                ALTER TABLE register_requests
                ALTER COLUMN school_id DROP NOT NULL;
            """))
            print("✅ Made school_id nullable in register_requests")
        else:
            print("ℹ️  school_id is already nullable, skipping")
    else:
        print("ℹ️  Table register_requests doesn't exist yet, skipping")


def downgrade() -> None:
    """Downgrade schema."""
    # Откатываем изменения - делаем school_id обязательным
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE register_requests
        ALTER COLUMN school_id SET NOT NULL;
    """))
