"""SQLAlchemy models for the ESG emissions feed, WACI metrics and override audit (RP-45)."""
from sqlalchemy import (
    Column, String, Numeric, DateTime, Integer, Text, ForeignKey,
    UniqueConstraint, Index, CheckConstraint,
)
from .database import Base


class EsgLoadBatch(Base):
    """One row per loader run of an inbound ESG file. file_sha256 makes re-runs of the same file a no-op."""
    __tablename__ = "esg_load_batches"

    batch_id = Column(String(36), primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_sha256 = Column(String(64), nullable=False, unique=True)
    as_of_month = Column(String(7))
    loaded_at = Column(DateTime, nullable=False)
    loaded_rows = Column(Integer, nullable=False, default=0)
    rejected_rows = Column(Integer, nullable=False, default=0)


class StgEsgEmissions(Base):
    """Staging copy of the monthly emissions feed, one row per (as_of_month, investment_id)."""
    __tablename__ = "stg_esg_emissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    load_batch_id = Column(String(36), ForeignKey("esg_load_batches.batch_id"), nullable=False)
    as_of_month = Column(String(7), nullable=False)
    investment_id = Column(String(10), nullable=False)
    scope1_tco2e = Column(Numeric(18, 4), nullable=False)
    scope2_tco2e = Column(Numeric(18, 4), nullable=False)
    revenue_musd = Column(Numeric(18, 4))
    source_row_no = Column(Integer)
    loaded_at = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint("as_of_month", "investment_id", name="uq_stg_esg_month_investment"),
        Index("idx_stg_esg_as_of_month", "as_of_month"),
    )


class EsgLoadReject(Base):
    """Rows from the feed that failed validation, with the reason, for the data provider to fix."""
    __tablename__ = "esg_load_rejects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    load_batch_id = Column(String(36), ForeignKey("esg_load_batches.batch_id"), nullable=False)
    source_row_no = Column(Integer, nullable=False)
    raw_row = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    rejected_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_esg_rejects_batch", "load_batch_id"),
    )


class PortfolioEsgMetrics(Base):
    """WACI per portfolio per as-of month, written by sql/esg_waci_v1.sql, plus the optional manual override."""
    __tablename__ = "portfolio_esg_metrics"

    portfolio_id = Column(String(8), primary_key=True)
    as_of_month = Column(String(7), primary_key=True)
    waci_computed = Column(Numeric(18, 6))
    coverage_pct = Column(Numeric(7, 4), nullable=False, default=0)
    total_market_value = Column(Numeric(18, 2), nullable=False, default=0)
    covered_market_value = Column(Numeric(18, 2), nullable=False, default=0)
    computed_at = Column(DateTime, nullable=False)
    override_value = Column(Numeric(18, 6))
    override_reason = Column(Text)
    override_by = Column(String(64))
    override_at = Column(DateTime)

    __table_args__ = (
        Index("idx_portfolio_esg_metrics_month", "as_of_month"),
    )

    @property
    def effective_value(self):
        return self.override_value if self.override_value is not None else self.waci_computed

    @property
    def source(self) -> str:
        return "override" if self.override_value is not None else "computed"


class EsgOverrideAudit(Base):
    """Append-only history of override set/clear actions. Rows are never updated or deleted."""
    __tablename__ = "esg_override_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(8), nullable=False)
    as_of_month = Column(String(7), nullable=False)
    action = Column(String(8), CheckConstraint("action IN ('OVERRIDE', 'CLEAR')"), nullable=False)
    old_value = Column(Numeric(18, 6))
    new_value = Column(Numeric(18, 6))
    reason = Column(Text, nullable=False)
    changed_by = Column(String(64), nullable=False)
    changed_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_esg_override_audit_portfolio", "portfolio_id", "as_of_month"),
        Index("idx_esg_override_audit_changed_at", "changed_at"),
    )
