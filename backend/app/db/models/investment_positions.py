"""
SQLAlchemy ORM model for the INVESTMENT_POSITIONS table.

Migrated from DB2 DDL in:
    COG-GTM/COBOL-Legacy-Benchmark-Suite  src/database/db2/db2-definitions.sql

Original DB2 definition
-----------------------
CREATE TABLE INVESTMENT_POSITIONS (
    PORTFOLIO_ID      CHAR(8)         NOT NULL,
    INVESTMENT_ID     CHAR(10)        NOT NULL,
    POSITION_DATE     DATE            NOT NULL,
    QUANTITY          DECIMAL(18,4)   NOT NULL,
    COST_BASIS        DECIMAL(18,2)   NOT NULL,
    MARKET_VALUE      DECIMAL(18,2)   NOT NULL,
    CURRENCY_CODE     CHAR(3)         NOT NULL,
    LAST_MAINT_DATE   TIMESTAMP       NOT NULL,
    LAST_MAINT_USER   VARCHAR(8)      NOT NULL,
    PRIMARY KEY (PORTFOLIO_ID, INVESTMENT_ID, POSITION_DATE),
    FOREIGN KEY (PORTFOLIO_ID) REFERENCES PORTFOLIO_MASTER(PORTFOLIO_ID)
);

Index: IDX_POSITIONS_DATE ON (POSITION_DATE, PORTFOLIO_ID)
"""

from sqlalchemy import Column, String, Date, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.database import Base


class InvestmentPosition(Base):
    """Investment position record — one row per portfolio/security/date.

    Maps to the DB2 INVESTMENT_POSITIONS table.  Uses a composite primary key
    (portfolio_id, investment_id, position_date) matching the original DDL.

    All financial amounts use Numeric to avoid floating-point rounding errors.
    """

    __tablename__ = "investment_positions"

    portfolio_id = Column(
        String(8),
        ForeignKey("portfolio_master.portfolio_id"),
        primary_key=True,
        nullable=False,
        comment="FK to portfolio_master (DB2 CHAR(8))",
    )
    investment_id = Column(String(10), primary_key=True, nullable=False,
                           comment="Security / investment identifier (DB2 CHAR(10))")
    position_date = Column(Date, primary_key=True, nullable=False,
                           comment="Valuation date for this position (DB2 DATE)")

    quantity = Column(Numeric(18, 4), nullable=False,
                      comment="Number of units held (DB2 DECIMAL(18,4))")
    cost_basis = Column(Numeric(18, 2), nullable=False,
                        comment="Total cost basis (DB2 DECIMAL(18,2))")
    market_value = Column(Numeric(18, 2), nullable=False,
                          comment="Current market value (DB2 DECIMAL(18,2))")
    currency_code = Column(String(3), nullable=False,
                           comment="ISO currency code (DB2 CHAR(3))")
    last_maint_date = Column(DateTime, nullable=False,
                             comment="Last maintenance timestamp (DB2 TIMESTAMP)")
    last_maint_user = Column(String(8), nullable=False,
                             comment="User who last modified the record (DB2 VARCHAR(8))")

    # --- Relationships ---------------------------------------------------
    portfolio = relationship("PortfolioMaster", back_populates="investment_positions")

    __table_args__ = (
        Index("idx_positions_date", "position_date", "portfolio_id"),
        {"comment": "Investment positions — migrated from DB2 INVESTMENT_POSITIONS (db2-definitions.sql)"},
    )

    def __repr__(self) -> str:
        return (
            f"<InvestmentPosition(portfolio_id={self.portfolio_id!r}, "
            f"investment_id={self.investment_id!r}, "
            f"position_date={self.position_date!r})>"
        )
