"""
SQLAlchemy ORM model for the TRANSACTION_HISTORY table.

Migrated from DB2 DDL in:
    COG-GTM/COBOL-Legacy-Benchmark-Suite  src/database/db2/db2-definitions.sql

Original DB2 definition
-----------------------
CREATE TABLE TRANSACTION_HISTORY (
    TRANSACTION_ID    CHAR(20)        NOT NULL,
    PORTFOLIO_ID      CHAR(8)         NOT NULL,
    TRANSACTION_DATE  DATE            NOT NULL,
    TRANSACTION_TIME  TIME            NOT NULL,
    INVESTMENT_ID     CHAR(10)        NOT NULL,
    TRANSACTION_TYPE  CHAR(2)         NOT NULL,
    QUANTITY          DECIMAL(18,4)   NOT NULL,
    PRICE             DECIMAL(18,4)   NOT NULL,
    AMOUNT            DECIMAL(18,2)   NOT NULL,
    CURRENCY_CODE     CHAR(3)         NOT NULL,
    STATUS            CHAR(1)         NOT NULL,
    PROCESS_DATE      TIMESTAMP       NOT NULL,
    PROCESS_USER      VARCHAR(8)      NOT NULL,
    PRIMARY KEY (TRANSACTION_ID),
    FOREIGN KEY (PORTFOLIO_ID) REFERENCES PORTFOLIO_MASTER(PORTFOLIO_ID)
);

Transaction types: 'BU'=Buy, 'SL'=Sell, 'TR'=Transfer, 'FE'=Fee
Status codes:      'P'=Processed, 'F'=Failed, 'R'=Reversed
TRANSACTION_ID format: YYYYMMDDHHMMSS + 6-digit sequence

Indexes:
    IDX_TRANS_HIST_PORT ON (PORTFOLIO_ID, TRANSACTION_DATE)
    IDX_TRANS_HIST_DATE ON (TRANSACTION_DATE, PORTFOLIO_ID)
"""

from sqlalchemy import Column, String, Date, Time, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.database import Base


class TransactionHistory(Base):
    """Transaction history record — one row per executed transaction.

    Maps to the DB2 TRANSACTION_HISTORY table.  The primary key is the 20-char
    TRANSACTION_ID (format: YYYYMMDDHHMMSS + 6-digit sequence).

    All financial amounts use Numeric to avoid floating-point rounding errors.
    """

    __tablename__ = "transaction_history"

    transaction_id = Column(String(20), primary_key=True, nullable=False,
                            comment="Unique transaction ID: YYYYMMDDHHMMSS + seq (DB2 CHAR(20))")
    portfolio_id = Column(
        String(8),
        ForeignKey("portfolio_master.portfolio_id"),
        nullable=False,
        comment="FK to portfolio_master (DB2 CHAR(8))",
    )
    transaction_date = Column(Date, nullable=False,
                              comment="Business date of the transaction (DB2 DATE)")
    transaction_time = Column(Time, nullable=False,
                              comment="Time of the transaction (DB2 TIME)")
    investment_id = Column(String(10), nullable=False,
                           comment="Security / investment identifier (DB2 CHAR(10))")
    transaction_type = Column(String(2), nullable=False,
                              comment="Type: BU=Buy, SL=Sell, TR=Transfer, FE=Fee (DB2 CHAR(2))")
    quantity = Column(Numeric(18, 4), nullable=False,
                      comment="Transaction quantity (DB2 DECIMAL(18,4))")
    price = Column(Numeric(18, 4), nullable=False,
                   comment="Transaction price per unit (DB2 DECIMAL(18,4))")
    amount = Column(Numeric(18, 2), nullable=False,
                    comment="Total transaction amount (DB2 DECIMAL(18,2))")
    currency_code = Column(String(3), nullable=False,
                           comment="ISO currency code (DB2 CHAR(3))")
    status = Column(String(1), nullable=False,
                    comment="Status: P=Processed, F=Failed, R=Reversed (DB2 CHAR(1))")
    process_date = Column(DateTime, nullable=False,
                          comment="Processing timestamp (DB2 TIMESTAMP)")
    process_user = Column(String(8), nullable=False,
                          comment="User who processed the transaction (DB2 VARCHAR(8))")

    # --- Relationships ---------------------------------------------------
    portfolio = relationship("PortfolioMaster", back_populates="transaction_history")

    __table_args__ = (
        Index("idx_trans_hist_port", "portfolio_id", "transaction_date"),
        Index("idx_trans_hist_date", "transaction_date", "portfolio_id"),
        {"comment": "Transaction history — migrated from DB2 TRANSACTION_HISTORY (db2-definitions.sql)"},
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionHistory(transaction_id={self.transaction_id!r}, "
            f"portfolio_id={self.portfolio_id!r}, status={self.status!r})>"
        )
