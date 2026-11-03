"""RP-50: ESG metric and override tables

Revision ID: b7e3c1d9a250
Revises: 40a256798f94
Create Date: 2026-11-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e3c1d9a250'
down_revision: Union[str, Sequence[str], None] = '40a256798f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('portfolio_esg_metrics',
    sa.Column('port_id', sa.String(length=8), nullable=False),
    sa.Column('as_of_month', sa.String(length=7), nullable=False),
    sa.Column('computed_value', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('coverage_pct', sa.Numeric(precision=7, scale=4), nullable=False),
    sa.Column('total_market_value', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('covered_market_value', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('positions_total', sa.Integer(), nullable=False),
    sa.Column('positions_covered', sa.Integer(), nullable=False),
    sa.Column('procedure_version', sa.String(length=20), nullable=False),
    sa.Column('computed_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['port_id'], ['portfolios.port_id'], ),
    sa.PrimaryKeyConstraint('port_id', 'as_of_month')
    )
    op.create_table('portfolio_esg_overrides',
    sa.Column('port_id', sa.String(length=8), nullable=False),
    sa.Column('as_of_month', sa.String(length=7), nullable=False),
    sa.Column('override_value', sa.Numeric(precision=18, scale=6), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('overridden_by', sa.String(length=8), nullable=False),
    sa.Column('overridden_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('override_value >= 0', name='ck_esg_override_value_non_negative'),
    sa.ForeignKeyConstraint(['port_id'], ['portfolios.port_id'], ),
    sa.PrimaryKeyConstraint('port_id', 'as_of_month')
    )
    op.create_index('idx_esg_override_port_month', 'portfolio_esg_overrides', ['port_id', 'as_of_month'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_esg_override_port_month', table_name='portfolio_esg_overrides')
    op.drop_table('portfolio_esg_overrides')
    op.drop_table('portfolio_esg_metrics')
