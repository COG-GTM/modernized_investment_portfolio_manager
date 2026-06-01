"""Drop history FK constraint for standalone audit log

Revision ID: aa2db1d56692
Revises: 40a256798f94
Create Date: 2026-03-12 06:42:43.672421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa2db1d56692'
down_revision: Union[str, Sequence[str], None] = '40a256798f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The History table is now a standalone audit log that must survive
    # entity deletion (mirrors COBOL audit file design).  Drop the FK
    # so that deleting a portfolio no longer cascades to or is blocked
    # by its audit records.
    with op.batch_alter_table('history') as batch_op:
        batch_op.drop_constraint(
            'fk_history_portfolio_id_portfolios',
            type_='foreignkey',
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('history') as batch_op:
        batch_op.create_foreign_key(
            'fk_history_portfolio_id_portfolios',
            'portfolios',
            ['portfolio_id'],
            ['port_id'],
        )
