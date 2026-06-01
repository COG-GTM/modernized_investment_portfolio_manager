"""
SQLAlchemy ORM model for the position_master table (VSAM replacement).

Migrated from VSAM KSDS definition in:
    COG-GTM/COBOL-Legacy-Benchmark-Suite  src/database/vsam/vsam-definitions.txt

Original VSAM definition (PORTMSTR)
------------------------------------
FILE NAME:        PORTMSTR
ORGANIZATION:     KSDS
RECORD FORMAT:    FIXED
RECORD LENGTH:    400
KEY LENGTH:       12
KEY POSITION:     1

Key Structure:
    - Portfolio ID  (8 bytes)
    - Account Type  (2 bytes)
    - Branch ID     (2 bytes)

Also incorporates the POSHIST VSAM file key structure for position records:
    - Portfolio ID   (8 bytes)
    - Position Date  (8 bytes, YYYYMMDD)
    - Investment ID  (10 bytes)

This table replaces the VSAM KSDS Position History file and provides a
relational equivalent that supports the same access patterns: primary key
look-ups and sequential date-range scans.
"""

from sqlalchemy import Column, String, Date, DateTime, Numeric, Index
from sqlalchemy.sql import func

from app.db.database import Base


class PositionMaster(Base):
    """Position master record — VSAM KSDS replacement for PORTMSTR / POSHIST.

    Composite primary key (portfolio_id, security_id) mirrors the VSAM key
    structure that combined Portfolio ID + Security/Investment ID for direct
    key-sequenced reads.

    Additional columns capture the full position state that was stored in the
    fixed-length 400-byte / 350-byte VSAM records.
    """

    __tablename__ = "position_master"

    # --- Composite primary key (mirrors VSAM key) -------------------------
    portfolio_id = Column(String(8), primary_key=True, nullable=False,
                          comment="Portfolio identifier — first 8 bytes of VSAM key")
    security_id = Column(String(12), primary_key=True, nullable=False,
                         comment="Security identifier — maps to VSAM POSHIST key bytes 17-26")

    # --- Portfolio identification (from PORTMSTR key) ---------------------
    account_type = Column(String(2), nullable=False,
                          comment="Account type — bytes 9-10 of PORTMSTR VSAM key")
    branch_id = Column(String(2), nullable=False,
                       comment="Branch identifier — bytes 11-12 of PORTMSTR VSAM key")

    # --- Position data ----------------------------------------------------
    position_date = Column(Date, nullable=False,
                           comment="Position valuation date (YYYYMMDD in VSAM)")
    quantity = Column(Numeric(18, 4), nullable=False,
                      comment="Number of units held")
    cost_basis = Column(Numeric(18, 2), nullable=False,
                        comment="Total cost basis")
    market_value = Column(Numeric(18, 2), nullable=False,
                          comment="Current market value")
    currency_code = Column(String(3), nullable=False,
                           comment="ISO currency code")
    status = Column(String(1), nullable=False,
                    comment="Position status: A=Active, C=Closed")

    # --- Audit fields -----------------------------------------------------
    last_maint_date = Column(DateTime, nullable=False, server_default=func.now(),
                             comment="Last maintenance timestamp")
    last_maint_user = Column(String(8), nullable=False,
                             comment="User who last modified the record")

    __table_args__ = (
        Index("idx_pos_master_date", "position_date", "portfolio_id"),
        Index("idx_pos_master_security", "security_id", "position_date"),
        {"comment": "Position master — VSAM KSDS replacement (vsam-definitions.txt PORTMSTR/POSHIST)"},
    )

    def __repr__(self) -> str:
        return (
            f"<PositionMaster(portfolio_id={self.portfolio_id!r}, "
            f"security_id={self.security_id!r})>"
        )
