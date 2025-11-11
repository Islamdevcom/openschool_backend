"""add_parent_role_and_parent_child_student_stats

Revision ID: b1a2c3d4e5f6
Revises: a31f93a2ae23
Create Date: 2025-11-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'a31f93a2ae23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Добавляем роль 'parent' в enum RoleEnum
    # Используем безопасный подход для PostgreSQL
    conn = op.get_bind()

    # Проверяем, существует ли уже значение 'parent'
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_enum
            WHERE enumlabel = 'parent'
            AND enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'roleenum'
            )
        );
    """))
    parent_exists = result.scalar()

    if not parent_exists:
        # Для PostgreSQL < 12: используем простой ALTER TYPE
        # Для PostgreSQL >= 12: используем IF NOT EXISTS
        # Обрабатываем обе версии
        try:
            # Попытка с IF NOT EXISTS (PostgreSQL 12+)
            conn.execute(sa.text("ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'parent'"))
        except sa.exc.DBAPIError:
            # Fallback для старых версий PostgreSQL
            try:
                conn.execute(sa.text("ALTER TYPE roleenum ADD VALUE 'parent'"))
            except sa.exc.DBAPIError as e:
                # Если значение уже существует - продолжаем
                if 'already exists' not in str(e):
                    raise

    # 2. Создаем таблицу parent_child
    op.create_table('parent_child',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_user_id', sa.Integer(), nullable=False),
        sa.Column('student_user_id', sa.Integer(), nullable=False),
        sa.Column('relationship', sa.String(length=50), nullable=True),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['parent_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('parent_user_id', 'student_user_id', name='uq_parent_student')
    )
    op.create_index(op.f('ix_parent_child_id'), 'parent_child', ['id'], unique=False)
    op.create_index('ix_parent_child_parent', 'parent_child', ['parent_user_id'], unique=False)
    op.create_index('ix_parent_child_student', 'parent_child', ['student_user_id'], unique=False)

    # 3. Создаем таблицу student_stats
    op.create_table('student_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_user_id', sa.Integer(), nullable=False),
        sa.Column('avg_grade', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('attendance', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('warnings', sa.Integer(), server_default='0', nullable=True),
        sa.Column('behavior', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_user_id')
    )
    op.create_index(op.f('ix_student_stats_id'), 'student_stats', ['id'], unique=False)
    op.create_index('ix_student_stats_user', 'student_stats', ['student_user_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем таблицы
    op.drop_index('ix_student_stats_user', table_name='student_stats')
    op.drop_index(op.f('ix_student_stats_id'), table_name='student_stats')
    op.drop_table('student_stats')

    op.drop_index('ix_parent_child_student', table_name='parent_child')
    op.drop_index('ix_parent_child_parent', table_name='parent_child')
    op.drop_index(op.f('ix_parent_child_id'), table_name='parent_child')
    op.drop_table('parent_child')

    # ВНИМАНИЕ: Удаление значения из enum в PostgreSQL невозможно без пересоздания типа
    # Поэтому оставляем 'parent' в enum даже при откате
    print("⚠️  Cannot remove 'parent' value from roleenum without recreating the type")
