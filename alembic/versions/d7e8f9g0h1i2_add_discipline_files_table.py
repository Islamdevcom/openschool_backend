"""add_discipline_files_table

Revision ID: d7e8f9g0h1i2
Revises: c1d2e3f4g5h6
Create Date: 2025-11-26 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd7e8f9g0h1i2'
down_revision = 'c1d2e3f4g5h6'
branch_labels = None
depends_on = None


def upgrade():
    # Create discipline_files table
    op.create_table(
        'discipline_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('discipline_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['discipline_id'], ['disciplines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_discipline_files_discipline_id'), 'discipline_files', ['discipline_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_discipline_files_discipline_id'), table_name='discipline_files')
    op.drop_table('discipline_files')
