from sqlalchemy import Column, String, Numeric, Integer, DateTime, Text, CheckConstraint, ForeignKeyConstraint, Index
from .database import Base


class PortfolioEsgMetric(Base):
    """WACI per portfolio and as-of month (written by the RP-47 procedure)."""

    __tablename__ = "portfolio_esg_metrics"

    port_id = Column(String(8), primary_key=True)
    as_of_month = Column(String(7), primary_key=True)

    computed_value = Column(Numeric(18, 6), nullable=True)
    coverage_pct = Column(Numeric(7, 4), nullable=False)
    total_market_value = Column(Numeric(18, 2), nullable=False)
    covered_market_value = Column(Numeric(18, 2), nullable=False)
    positions_total = Column(Integer, nullable=False)
    positions_covered = Column(Integer, nullable=False)
    procedure_version = Column(String(20), nullable=False)
    computed_at = Column(DateTime, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['port_id'], ['portfolios.port_id']),
    )


class PortfolioEsgOverride(Base):
    """Manager override of the effective WACI, at most one per portfolio-month."""

    __tablename__ = "portfolio_esg_overrides"

    port_id = Column(String(8), primary_key=True)
    as_of_month = Column(String(7), primary_key=True)

    override_value = Column(Numeric(18, 6), nullable=False)
    reason = Column(Text, nullable=False)
    overridden_by = Column(String(8), nullable=False)
    overridden_at = Column(DateTime, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['port_id'], ['portfolios.port_id']),
        CheckConstraint("override_value >= 0", name="ck_esg_override_value_non_negative"),
        Index('idx_esg_override_port_month', 'port_id', 'as_of_month'),
    )
