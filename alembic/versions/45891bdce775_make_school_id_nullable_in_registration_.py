"""make school_id nullable in registration_requests

Revision ID: 45891bdce775
Revises: ea139294a4c6
Create Date: 2025-10-30 19:35:13.510770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45891bdce775'
down_revision: Union[str, Sequence[str], None] = 'ea139294a4c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Делаем school_id nullable для поддержки индивидуальной регистрации
    op.alter_column('register_requests', 'school_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Откатываем изменения - делаем school_id обязательным
    op.alter_column('register_requests', 'school_id',
                    existing_type=sa.Integer(),
                    nullable=False)
