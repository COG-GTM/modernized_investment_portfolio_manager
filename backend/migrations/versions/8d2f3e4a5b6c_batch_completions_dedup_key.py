"""Batch completions: unique idempotency key per logical job

Revision ID: 8d2f3e4a5b6c
Revises: 7c1e2d3f4a5b
Create Date: 2026-09-23 02:40:00.000000

Adds ``batch_completions.dedup_key`` (the logical job id) with a unique index so storage
itself rejects a second completion for the same job. Existing rows are backfilled only for
jobs that currently have exactly one completion; jobs that already carry duplicate rows are
left with a NULL key (SQLite unique indexes ignore NULLs) so that evidence is preserved and
the migration never fails on a database that has recorded the fault.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8d2f3e4a5b6c'
down_revision: Union[str, Sequence[str], None] = '7c1e2d3f4a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('batch_completions', sa.Column('dedup_key', sa.String(length=64), nullable=True))
    op.execute(
        """
        UPDATE batch_completions
        SET dedup_key = job_id
        WHERE job_id IN (
            SELECT job_id FROM batch_completions GROUP BY job_id HAVING COUNT(*) = 1
        )
        """
    )
    op.create_index('uq_batch_completions_dedup_key', 'batch_completions', ['dedup_key'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_batch_completions_dedup_key', table_name='batch_completions')
    with op.batch_alter_table('batch_completions') as batch_op:
        batch_op.drop_column('dedup_key')
