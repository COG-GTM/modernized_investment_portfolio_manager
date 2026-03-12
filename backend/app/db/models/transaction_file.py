"""
SQLAlchemy ORM model for the transaction_file table (VSAM replacement).

Migrated from VSAM KSDS definition in:
    COG-GTM/COBOL-Legacy-Benchmark-Suite  src/database/vsam/vsam-definitions.txt

Original VSAM definition (TRANHIST)
------------------------------------
FILE NAME:        TRANHIST
ORGANIZATION:     KSDS
RECORD FORMAT:    FIXED
RECORD LENGTH:    300
KEY LENGTH:       20
KEY POSITION:     1

Key Structure:
    - Transaction Date   (8 bytes, YYYYMMDD)
    - Transaction Time   (6 bytes, HHMMSS)
    - Portfolio ID       (8 bytes)
    - Sequence Number    (6 bytes)

This table replaces the VSAM KSDS Transaction History file and provides a
relational equivalent supporting key-sequenced reads and sequential scans
by date range.
"""

from sqlalchemy import Column, String, Date, Time, DateTime, Numeric, Index
from sqlalchemy.sql import func

from app.db.database import Base


class TransactionFile(Base):
    """Transaction file record — VSAM KSDS replacement for TRANHIST.

    Composite primary key (transaction_date, transaction_time, portfolio_id,
    sequence_no) mirrors the 20-byte VSAM key structure for direct look-ups
    and sequential date-range scans.

    All financial amounts use Numeric to avoid floating-point rounding errors.
    """

    __tablename__ = "transaction_file"

    # --- Composite primary key (mirrors 20-byte VSAM key) -----------------
    transaction_date = Column(Date, primary_key=True, nullable=False,
                              comment="Transaction date — bytes 1-8 of VSAM key (YYYYMMDD)")
    transaction_time = Column(Time, primary_key=True, nullable=False,
                              comment="Transaction time — bytes 9-14 of VSAM key (HHMMSS)")
    portfolio_id = Column(String(8), primary_key=True, nullable=False,
                          comment="Portfolio identifier — bytes 15-22 of VSAM key")
    sequence_no = Column(String(6), primary_key=True, nullable=False,
                         comment="Sequence number — bytes 23-28 of VSAM key")

    # --- Transaction data -------------------------------------------------
    investment_id = Column(String(10), nullable=False,
                           comment="Security / investment identifier")
    transaction_type = Column(String(2), nullable=False,
                              comment="Type: BU=Buy, SL=Sell, TR=Transfer, FE=Fee")
    quantity = Column(Numeric(18, 4), nullable=False,
                      comment="Transaction quantity")
    price = Column(Numeric(18, 4), nullable=False,
                   comment="Price per unit")
    amount = Column(Numeric(18, 2), nullable=False,
                    comment="Transaction amount (quantity * price)")
    currency_code = Column(String(3), nullable=False,
                           comment="ISO currency code")
    status = Column(String(1), nullable=False,
                    comment="Status: P=Processed, F=Failed, R=Reversed")

    # --- Audit fields -----------------------------------------------------
    process_timestamp = Column(DateTime, nullable=False, server_default=func.now(),
                               comment="Processing timestamp")
    process_user = Column(String(8), nullable=False,
                          comment="User who processed the transaction")

    __table_args__ = (
        Index("idx_txn_file_portfolio", "portfolio_id", "transaction_date"),
        Index("idx_txn_file_date", "transaction_date", "portfolio_id"),
        {"comment": "Transaction file — VSAM KSDS replacement (vsam-definitions.txt TRANHIST)"},
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionFile(transaction_date={self.transaction_date!r}, "
            f"portfolio_id={self.portfolio_id!r}, "
            f"sequence_no={self.sequence_no!r})>"
        )
