"""Add AI tools tables and fields

Revision ID: c1d2e3f4g5h6
Revises: b1a2c3d4e5f6
Create Date: 2024-11-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: Union[str, None] = 'b1a2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поля в student_activities для AI-инструментов
    # Используем batch mode для SQLite совместимости
    with op.batch_alter_table('student_activities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('activity_type', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('tasks_total', sa.Integer(), nullable=True, server_default='1'))
        batch_op.add_column(sa.Column('tasks_completed', sa.Integer(), nullable=True, server_default='0'))

    # Создаем таблицу generated_contents для хранения сгенерированного контента
    op.create_table(
        'generated_contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=True),
        sa.Column('tool_type', sa.String(100), nullable=False),
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('topic', sa.String(255), nullable=True),
        sa.Column('grade_level', sa.String(50), nullable=True),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('language', sa.String(10), nullable=True, server_default='ru'),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_contents_id'), 'generated_contents', ['id'], unique=False)
    op.create_index(op.f('ix_generated_contents_teacher_id'), 'generated_contents', ['teacher_id'], unique=False)
    op.create_index(op.f('ix_generated_contents_tool_type'), 'generated_contents', ['tool_type'], unique=False)

    # Создаем таблицу tool_usage_logs для логирования использования инструментов
    op.create_table(
        'tool_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=True),
        sa.Column('tool_type', sa.String(100), nullable=False),
        sa.Column('request_params', sa.JSON(), nullable=True),
        sa.Column('success', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_usage_logs_id'), 'tool_usage_logs', ['id'], unique=False)
    op.create_index(op.f('ix_tool_usage_logs_teacher_id'), 'tool_usage_logs', ['teacher_id'], unique=False)
    op.create_index(op.f('ix_tool_usage_logs_tool_type'), 'tool_usage_logs', ['tool_type'], unique=False)


def downgrade() -> None:
    # Удаляем таблицу tool_usage_logs
    op.drop_index(op.f('ix_tool_usage_logs_tool_type'), table_name='tool_usage_logs')
    op.drop_index(op.f('ix_tool_usage_logs_teacher_id'), table_name='tool_usage_logs')
    op.drop_index(op.f('ix_tool_usage_logs_id'), table_name='tool_usage_logs')
    op.drop_table('tool_usage_logs')

    # Удаляем таблицу generated_contents
    op.drop_index(op.f('ix_generated_contents_tool_type'), table_name='generated_contents')
    op.drop_index(op.f('ix_generated_contents_teacher_id'), table_name='generated_contents')
    op.drop_index(op.f('ix_generated_contents_id'), table_name='generated_contents')
    op.drop_table('generated_contents')

    # Удаляем поля из student_activities
    with op.batch_alter_table('student_activities', schema=None) as batch_op:
        batch_op.drop_column('tasks_completed')
        batch_op.drop_column('tasks_total')
        batch_op.drop_column('activity_type')
