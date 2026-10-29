from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)

from .database import Base


class EsgLoadBatch(Base):
    """One row per ESG feed file the loader has processed."""

    __tablename__ = "esg_load_batches"

    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(255), nullable=False)
    file_sha256 = Column(String(64), nullable=False, index=True)
    as_of_month = Column(String(7), nullable=False)
    loaded_at = Column(DateTime, nullable=False)
    row_count = Column(Integer, nullable=False)
    accepted_count = Column(Integer, nullable=False)
    rejected_count = Column(Integer, nullable=False)
    status = Column(String(1), CheckConstraint("status IN ('C', 'F')", name="ck_esg_load_batches_status"), nullable=False)
    failure_reason = Column(String(30))

    __table_args__ = (Index("idx_esg_load_batches_month", "as_of_month"),)


class StgEsgEmission(Base):
    """Staged emissions, one row per holding per month (the month's latest accepted snapshot)."""

    __tablename__ = "stg_esg_emissions"

    as_of_month = Column(String(7), primary_key=True)
    investment_id = Column(String(10), primary_key=True)
    scope1_tco2e = Column(Numeric(18, 4), nullable=False)
    scope2_tco2e = Column(Numeric(18, 4), nullable=False)
    revenue_musd = Column(Numeric(18, 4))
    batch_id = Column(Integer, ForeignKey("esg_load_batches.batch_id"), nullable=False)
    source_row_no = Column(Integer, nullable=False)
    loaded_at = Column(DateTime, nullable=False)

    __table_args__ = (Index("idx_stg_esg_batch_id", "batch_id"),)


class EsgLoadReject(Base):
    """Feed rows the loader refused, with the reason code."""

    __tablename__ = "esg_load_rejects"

    reject_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("esg_load_batches.batch_id"), nullable=False)
    source_row_no = Column(Integer, nullable=False)
    raw_line = Column(Text, nullable=False)
    reason = Column(String(200), nullable=False)
    rejected_at = Column(DateTime, nullable=False)

    __table_args__ = (Index("idx_esg_load_rejects_batch_id", "batch_id"),)
