"""
SQLAlchemy ORM model for the PORTFOLIO_MASTER table.

Migrated from DB2 DDL in:
    COG-GTM/COBOL-Legacy-Benchmark-Suite  src/database/db2/db2-definitions.sql

Original DB2 definition
-----------------------
CREATE TABLE PORTFOLIO_MASTER (
    PORTFOLIO_ID      CHAR(8)         NOT NULL,
    ACCOUNT_TYPE      CHAR(2)         NOT NULL,
    BRANCH_ID         CHAR(2)         NOT NULL,
    CLIENT_ID         CHAR(10)        NOT NULL,
    PORTFOLIO_NAME    VARCHAR(50)     NOT NULL,
    CURRENCY_CODE     CHAR(3)         NOT NULL,
    RISK_LEVEL        CHAR(1)         NOT NULL,
    STATUS            CHAR(1)         NOT NULL,
    OPEN_DATE         DATE            NOT NULL,
    CLOSE_DATE        DATE,
    LAST_MAINT_DATE   TIMESTAMP       NOT NULL,
    LAST_MAINT_USER   VARCHAR(8)      NOT NULL,
    PRIMARY KEY (PORTFOLIO_ID)
);

Status codes: 'A'=Active, 'C'=Closed, 'S'=Suspended
"""

from sqlalchemy import Column, String, Date, DateTime, Index
from sqlalchemy.orm import relationship

from app.db.database import Base


class PortfolioMaster(Base):
    """Portfolio master record — one row per portfolio.

    Maps to the DB2 PORTFOLIO_MASTER table.  The primary key is the 8-char
    PORTFOLIO_ID.  An index on (CLIENT_ID, STATUS) mirrors the original
    IDX_PORT_MASTER_CLIENT index used for client look-ups.
    """

    __tablename__ = "portfolio_master"

    portfolio_id = Column(String(8), primary_key=True, nullable=False,
                          comment="Portfolio identifier (DB2 CHAR(8))")
    account_type = Column(String(2), nullable=False,
                          comment="Account type code (DB2 CHAR(2))")
    branch_id = Column(String(2), nullable=False,
                       comment="Branch identifier (DB2 CHAR(2))")
    client_id = Column(String(10), nullable=False,
                       comment="Client identifier (DB2 CHAR(10))")
    portfolio_name = Column(String(50), nullable=False,
                            comment="Portfolio display name (DB2 VARCHAR(50))")
    currency_code = Column(String(3), nullable=False,
                           comment="ISO currency code (DB2 CHAR(3))")
    risk_level = Column(String(1), nullable=False,
                        comment="Risk level indicator (DB2 CHAR(1))")
    status = Column(String(1), nullable=False,
                    comment="Portfolio status: A=Active, C=Closed, S=Suspended")
    open_date = Column(Date, nullable=False,
                       comment="Date portfolio was opened (DB2 DATE)")
    close_date = Column(Date, nullable=True,
                        comment="Date portfolio was closed, NULL if open (DB2 DATE)")
    last_maint_date = Column(DateTime, nullable=False,
                             comment="Last maintenance timestamp (DB2 TIMESTAMP)")
    last_maint_user = Column(String(8), nullable=False,
                             comment="User who last modified the record (DB2 VARCHAR(8))")

    # --- Relationships ---------------------------------------------------
    investment_positions = relationship(
        "InvestmentPosition",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )
    transaction_history = relationship(
        "TransactionHistory",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_port_master_client", "client_id", "status"),
        {"comment": "Portfolio master — migrated from DB2 PORTFOLIO_MASTER (db2-definitions.sql)"},
    )

    def __repr__(self) -> str:
        return (
            f"<PortfolioMaster(portfolio_id={self.portfolio_id!r}, "
            f"client_id={self.client_id!r}, status={self.status!r})>"
        )
