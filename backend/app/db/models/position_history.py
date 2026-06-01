"""
SQLAlchemy ORM model for the POSHIST (Position History) table.

Migrated from DB2 DDL in:
    COG-GTM/COBOL-Legacy-Benchmark-Suite  src/database/db2/POSHIST.sql

Original DB2 definition
-----------------------
CREATE TABLE POSHIST (
    ACCOUNT_NO        CHAR(8)         NOT NULL,
    PORTFOLIO_ID      CHAR(10)        NOT NULL,
    TRANS_DATE        DATE            NOT NULL,
    TRANS_TIME        TIME            NOT NULL,
    TRANS_TYPE        CHAR(2)         NOT NULL,
    SECURITY_ID       CHAR(12)        NOT NULL,
    QUANTITY          DECIMAL(15,3)   NOT NULL,
    PRICE             DECIMAL(15,3)   NOT NULL,
    AMOUNT            DECIMAL(15,2)   NOT NULL,
    FEES              DECIMAL(15,2)   NOT NULL WITH DEFAULT 0,
    TOTAL_AMOUNT      DECIMAL(15,2)   NOT NULL,
    COST_BASIS        DECIMAL(15,2)   NOT NULL,
    GAIN_LOSS         DECIMAL(15,2)   NOT NULL,
    PROCESS_DATE      DATE            NOT NULL,
    PROCESS_TIME      TIME            NOT NULL,
    PROGRAM_ID        CHAR(8)         NOT NULL,
    USER_ID           CHAR(8)         NOT NULL,
    AUDIT_TIMESTAMP   TIMESTAMP       NOT NULL WITH DEFAULT
);

Composite PK: (ACCOUNT_NO, PORTFOLIO_ID, TRANS_DATE, TRANS_TIME)

Indexes:
    POSHIST_IX1 ON (SECURITY_ID, TRANS_DATE)
    POSHIST_IX2 ON (PROCESS_DATE, PROGRAM_ID)

Transaction types: BU=Buy, SL=Sell, TR=Transfer

Note: The original DB2 table was range-partitioned by TRANS_DATE (quarterly).
PostgreSQL native partitioning can be applied later if needed; this model
defines the logical schema without partitioning.
"""

from sqlalchemy import Column, String, Date, Time, DateTime, Numeric, Index
from sqlalchemy.sql import func

from app.db.database import Base


class PositionHistory(Base):
    """Position history record — stores all portfolio transaction history.

    Maps to the DB2 POSHIST table (POSHIST.sql).  Uses a composite primary key
    (account_no, portfolio_id, trans_date, trans_time) matching the original
    clustered unique index POSHIST_PK.

    All financial amounts use Numeric to avoid floating-point rounding errors.
    """

    __tablename__ = "position_history"

    # --- Composite primary key (matches POSHIST_PK) ----------------------
    account_no = Column(String(8), primary_key=True, nullable=False,
                        comment="Account number (DB2 CHAR(8))")
    portfolio_id = Column(String(10), primary_key=True, nullable=False,
                          comment="Portfolio identifier (DB2 CHAR(10))")
    trans_date = Column(Date, primary_key=True, nullable=False,
                        comment="Transaction date (DB2 DATE)")
    trans_time = Column(Time, primary_key=True, nullable=False,
                        comment="Transaction time (DB2 TIME)")

    # --- Data columns -----------------------------------------------------
    trans_type = Column(String(2), nullable=False,
                        comment="Transaction type: BU=Buy, SL=Sell, TR=Transfer (DB2 CHAR(2))")
    security_id = Column(String(12), nullable=False,
                         comment="Security identifier (DB2 CHAR(12))")
    quantity = Column(Numeric(15, 3), nullable=False,
                      comment="Transaction quantity (DB2 DECIMAL(15,3))")
    price = Column(Numeric(15, 3), nullable=False,
                   comment="Transaction price per unit (DB2 DECIMAL(15,3))")
    amount = Column(Numeric(15, 2), nullable=False,
                    comment="Transaction amount (DB2 DECIMAL(15,2))")
    fees = Column(Numeric(15, 2), nullable=False, server_default="0",
                  comment="Transaction fees (DB2 DECIMAL(15,2) DEFAULT 0)")
    total_amount = Column(Numeric(15, 2), nullable=False,
                          comment="Total amount including fees (DB2 DECIMAL(15,2))")
    cost_basis = Column(Numeric(15, 2), nullable=False,
                        comment="Cost basis amount (DB2 DECIMAL(15,2))")
    gain_loss = Column(Numeric(15, 2), nullable=False,
                       comment="Realized gain/loss amount (DB2 DECIMAL(15,2))")

    # --- Audit columns ----------------------------------------------------
    process_date = Column(Date, nullable=False,
                          comment="Processing date (DB2 DATE)")
    process_time = Column(Time, nullable=False,
                          comment="Processing time (DB2 TIME)")
    program_id = Column(String(8), nullable=False,
                        comment="Originating program ID (DB2 CHAR(8))")
    user_id = Column(String(8), nullable=False,
                     comment="User who processed the record (DB2 CHAR(8))")
    audit_timestamp = Column(DateTime, nullable=False, server_default=func.now(),
                             comment="Audit timestamp (DB2 TIMESTAMP WITH DEFAULT)")

    __table_args__ = (
        Index("poshist_ix1", "security_id", "trans_date"),
        Index("poshist_ix2", "process_date", "program_id"),
        {"comment": "Position history — migrated from DB2 POSHIST (POSHIST.sql)"},
    )

    def __repr__(self) -> str:
        return (
            f"<PositionHistory(account_no={self.account_no!r}, "
            f"portfolio_id={self.portfolio_id!r}, "
            f"trans_date={self.trans_date!r})>"
        )
