"""RP-51 enforce append-only esg_override_audit at the database level

Revision ID: 9c1e2a7d4b55
Revises: fabc3d71f83b
Create Date: 2026-10-29 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '9c1e2a7d4b55'
down_revision: Union[str, Sequence[str], None] = 'fabc3d71f83b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Block UPDATE and DELETE on the audit table so the trail cannot be rewritten by any route."""
    op.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_esg_override_audit_no_update BEFORE UPDATE ON esg_override_audit "
        "BEGIN SELECT RAISE(ABORT, 'esg_override_audit is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_esg_override_audit_no_delete BEFORE DELETE ON esg_override_audit "
        "BEGIN SELECT RAISE(ABORT, 'esg_override_audit is append-only'); END"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_esg_override_audit_no_update")
    op.execute("DROP TRIGGER IF EXISTS trg_esg_override_audit_no_delete")
