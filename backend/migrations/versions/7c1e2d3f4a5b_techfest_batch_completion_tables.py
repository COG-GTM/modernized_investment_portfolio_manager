"""Batch-completion service tables (synthetic demonstration)

Revision ID: 7c1e2d3f4a5b
Revises: 40a256798f94
Create Date: 2026-09-23 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7c1e2d3f4a5b'
down_revision: Union[str, Sequence[str], None] = '40a256798f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'batch_jobs',
        sa.Column('job_id', sa.String(length=64), nullable=False),
        sa.Column('run_date', sa.String(length=8), nullable=False),
        sa.Column('portfolio_id', sa.String(length=8), nullable=False),
        sa.Column('job_type', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=12), nullable=False),
        sa.Column('transaction_count', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.String(length=24), nullable=False),
        sa.Column('fault_injection', sa.String(length=24), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('job_id'),
    )
    op.create_index('idx_batch_jobs_run_date', 'batch_jobs', ['run_date'], unique=False)
    op.create_index('idx_batch_jobs_portfolio', 'batch_jobs', ['portfolio_id'], unique=False)
    op.create_table(
        'batch_completions',
        sa.Column('completion_id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=64), nullable=False),
        sa.Column('attempt', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=False),
        sa.Column('code_revision', sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['batch_jobs.job_id']),
        sa.PrimaryKeyConstraint('completion_id'),
    )
    op.create_index('idx_batch_completions_job_id', 'batch_completions', ['job_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_batch_completions_job_id', table_name='batch_completions')
    op.drop_table('batch_completions')
    op.drop_index('idx_batch_jobs_portfolio', table_name='batch_jobs')
    op.drop_index('idx_batch_jobs_run_date', table_name='batch_jobs')
    op.drop_table('batch_jobs')
