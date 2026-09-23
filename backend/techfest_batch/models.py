from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from models.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    job_id = Column(String(64), primary_key=True)
    run_date = Column(String(8), nullable=False)
    portfolio_id = Column(String(8), nullable=False)
    job_type = Column(String(16), nullable=False, default="EOD_POST")
    status = Column(String(12), nullable=False, default="PENDING")
    transaction_count = Column(Integer, nullable=False, default=0)
    # Decimal string in fixed 2dp; never a float.
    total_amount = Column(String(24), nullable=False, default="0.00")
    fault_injection = Column(String(24), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    completions = relationship(
        "BatchCompletion", back_populates="job", order_by="BatchCompletion.completed_at"
    )

    __table_args__ = (
        Index("idx_batch_jobs_run_date", "run_date"),
        Index("idx_batch_jobs_portfolio", "portfolio_id"),
    )

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "run_date": self.run_date,
            "portfolio_id": self.portfolio_id,
            "job_type": self.job_type,
            "status": self.status,
            "transaction_count": self.transaction_count,
            "total_amount": self.total_amount,
            "fault_injection": self.fault_injection,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BatchCompletion(Base):
    __tablename__ = "batch_completions"

    completion_id = Column(String(36), primary_key=True)
    job_id = Column(String(64), ForeignKey("batch_jobs.job_id"), nullable=False)
    attempt = Column(Integer, nullable=False)
    request_id = Column(String(36), nullable=False)
    completed_at = Column(DateTime, nullable=False, default=utcnow)
    code_revision = Column(String(40), nullable=False)

    job = relationship("BatchJob", back_populates="completions")

    __table_args__ = (Index("idx_batch_completions_job_id", "job_id"),)

    def to_dict(self) -> dict:
        return {
            "completion_id": self.completion_id,
            "job_id": self.job_id,
            "attempt": self.attempt,
            "request_id": self.request_id,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "code_revision": self.code_revision,
        }
