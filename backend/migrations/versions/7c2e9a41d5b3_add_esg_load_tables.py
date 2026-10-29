"""Add ESG feed load tables (SSTCNTRL-2)

Revision ID: 7c2e9a41d5b3
Revises: 40a256798f94
Create Date: 2026-10-29 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7c2e9a41d5b3'
down_revision: Union[str, Sequence[str], None] = '40a256798f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'esg_load_batches',
        sa.Column('batch_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('file_sha256', sa.String(length=64), nullable=False),
        sa.Column('as_of_month', sa.String(length=7), nullable=False),
        sa.Column('loaded_at', sa.DateTime(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('accepted_count', sa.Integer(), nullable=False),
        sa.Column('rejected_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=1), nullable=False),
        sa.Column('failure_reason', sa.String(length=30), nullable=True),
        sa.CheckConstraint("status IN ('C', 'F')", name='ck_esg_load_batches_status'),
        sa.PrimaryKeyConstraint('batch_id'),
    )
    op.create_index('idx_esg_load_batches_month', 'esg_load_batches', ['as_of_month'], unique=False)
    op.create_index(op.f('ix_esg_load_batches_file_sha256'), 'esg_load_batches', ['file_sha256'], unique=False)

    op.create_table(
        'stg_esg_emissions',
        sa.Column('as_of_month', sa.String(length=7), nullable=False),
        sa.Column('investment_id', sa.String(length=10), nullable=False),
        sa.Column('scope1_tco2e', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('scope2_tco2e', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('revenue_musd', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('source_row_no', sa.Integer(), nullable=False),
        sa.Column('loaded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['esg_load_batches.batch_id']),
        sa.PrimaryKeyConstraint('as_of_month', 'investment_id'),
    )
    op.create_index('idx_stg_esg_batch_id', 'stg_esg_emissions', ['batch_id'], unique=False)

    op.create_table(
        'esg_load_rejects',
        sa.Column('reject_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('source_row_no', sa.Integer(), nullable=False),
        sa.Column('raw_line', sa.Text(), nullable=False),
        sa.Column('reason', sa.String(length=200), nullable=False),
        sa.Column('rejected_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['esg_load_batches.batch_id']),
        sa.PrimaryKeyConstraint('reject_id'),
    )
    op.create_index('idx_esg_load_rejects_batch_id', 'esg_load_rejects', ['batch_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_esg_load_rejects_batch_id', table_name='esg_load_rejects')
    op.drop_table('esg_load_rejects')
    op.drop_index('idx_stg_esg_batch_id', table_name='stg_esg_emissions')
    op.drop_table('stg_esg_emissions')
    op.drop_index(op.f('ix_esg_load_batches_file_sha256'), table_name='esg_load_batches')
    op.drop_index('idx_esg_load_batches_month', table_name='esg_load_batches')
    op.drop_table('esg_load_batches')
