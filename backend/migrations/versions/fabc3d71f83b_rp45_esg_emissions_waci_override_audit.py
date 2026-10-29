"""RP-45 ESG emissions staging, WACI metrics and override audit

Revision ID: fabc3d71f83b
Revises: 40a256798f94
Create Date: 2026-10-29 14:41:33.078063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fabc3d71f83b'
down_revision: Union[str, Sequence[str], None] = '40a256798f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('esg_load_batches',
    sa.Column('batch_id', sa.String(length=36), nullable=False),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('file_sha256', sa.String(length=64), nullable=False),
    sa.Column('as_of_month', sa.String(length=7), nullable=True),
    sa.Column('loaded_at', sa.DateTime(), nullable=False),
    sa.Column('loaded_rows', sa.Integer(), nullable=False),
    sa.Column('rejected_rows', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('batch_id'),
    sa.UniqueConstraint('file_sha256')
    )
    op.create_table('esg_override_audit',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('portfolio_id', sa.String(length=8), nullable=False),
    sa.Column('as_of_month', sa.String(length=7), nullable=False),
    sa.Column('action', sa.String(length=8), nullable=False),
    sa.CheckConstraint("action IN ('OVERRIDE', 'CLEAR')", name='ck_esg_override_audit_action'),
    sa.Column('old_value', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('new_value', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('changed_by', sa.String(length=64), nullable=False),
    sa.Column('changed_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_esg_override_audit_changed_at', 'esg_override_audit', ['changed_at'], unique=False)
    op.create_index('idx_esg_override_audit_portfolio', 'esg_override_audit', ['portfolio_id', 'as_of_month'], unique=False)
    op.create_table('portfolio_esg_metrics',
    sa.Column('portfolio_id', sa.String(length=8), nullable=False),
    sa.Column('as_of_month', sa.String(length=7), nullable=False),
    sa.Column('waci_computed', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('coverage_pct', sa.Numeric(precision=7, scale=4), nullable=False),
    sa.Column('total_market_value', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('covered_market_value', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('computed_at', sa.DateTime(), nullable=False),
    sa.Column('override_value', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('override_reason', sa.Text(), nullable=True),
    sa.Column('override_by', sa.String(length=64), nullable=True),
    sa.Column('override_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('portfolio_id', 'as_of_month')
    )
    op.create_index('idx_portfolio_esg_metrics_month', 'portfolio_esg_metrics', ['as_of_month'], unique=False)
    op.create_table('esg_load_rejects',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('load_batch_id', sa.String(length=36), nullable=False),
    sa.Column('source_row_no', sa.Integer(), nullable=False),
    sa.Column('raw_row', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('rejected_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['load_batch_id'], ['esg_load_batches.batch_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_esg_rejects_batch', 'esg_load_rejects', ['load_batch_id'], unique=False)
    op.create_table('stg_esg_emissions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('load_batch_id', sa.String(length=36), nullable=False),
    sa.Column('as_of_month', sa.String(length=7), nullable=False),
    sa.Column('investment_id', sa.String(length=10), nullable=False),
    sa.Column('scope1_tco2e', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('scope2_tco2e', sa.Numeric(precision=18, scale=4), nullable=False),
    sa.Column('revenue_musd', sa.Numeric(precision=18, scale=4), nullable=True),
    sa.Column('source_row_no', sa.Integer(), nullable=True),
    sa.Column('loaded_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['load_batch_id'], ['esg_load_batches.batch_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('as_of_month', 'investment_id', name='uq_stg_esg_month_investment')
    )
    op.create_index('idx_stg_esg_as_of_month', 'stg_esg_emissions', ['as_of_month'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_stg_esg_as_of_month', table_name='stg_esg_emissions')
    op.drop_table('stg_esg_emissions')
    op.drop_index('idx_esg_rejects_batch', table_name='esg_load_rejects')
    op.drop_table('esg_load_rejects')
    op.drop_index('idx_portfolio_esg_metrics_month', table_name='portfolio_esg_metrics')
    op.drop_table('portfolio_esg_metrics')
    op.drop_index('idx_esg_override_audit_portfolio', table_name='esg_override_audit')
    op.drop_index('idx_esg_override_audit_changed_at', table_name='esg_override_audit')
    op.drop_table('esg_override_audit')
    op.drop_table('esg_load_batches')
