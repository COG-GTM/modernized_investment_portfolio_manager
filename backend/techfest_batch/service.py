import time
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from techfest_batch.config import FAULT_PRE_ACK_STALL, settings
from techfest_batch.models import BatchCompletion, BatchJob, utcnow


class JobNotFound(LookupError):
    pass


@dataclass
class CompletionResult:
    completion: BatchCompletion
    deduplicated: bool
    stalled_ms: int = 0

    def to_dict(self) -> dict:
        data = self.completion.to_dict()
        data["deduplicated"] = self.deduplicated
        data["stalled_ms"] = self.stalled_ms
        return data


def pre_ack_stall_ms(job: BatchJob, attempt: int) -> int:
    """Fault injector: deterministic delay before acknowledging the first attempt of a flagged job."""
    if not settings.fault_injection_enabled:
        return 0
    if job.fault_injection != FAULT_PRE_ACK_STALL or attempt != 1:
        return 0
    return settings.stall_ms


def complete_job(session: Session, job_id: str, request_id: str, attempt: int) -> CompletionResult:
    job = session.get(BatchJob, job_id)
    if job is None:
        raise JobNotFound(job_id)

    replayed = session.scalar(
        select(BatchCompletion).where(BatchCompletion.request_id == request_id)
    )
    if replayed is not None:
        return CompletionResult(replayed, deduplicated=True)

    completion = BatchCompletion(
        completion_id=str(uuid.uuid4()),
        job_id=job.job_id,
        attempt=attempt,
        request_id=request_id,
        completed_at=utcnow(),
        code_revision=settings.code_revision,
    )
    job.status = "COMPLETED"
    session.add(completion)
    session.commit()

    stall = pre_ack_stall_ms(job, attempt)
    if stall:
        time.sleep(stall / 1000.0)
    return CompletionResult(completion, deduplicated=False, stalled_ms=stall)


def list_jobs(session: Session) -> list[BatchJob]:
    return list(session.scalars(select(BatchJob).order_by(BatchJob.run_date, BatchJob.job_id)))


def completions_for_job(session: Session, job_id: str) -> list[BatchCompletion]:
    return list(
        session.scalars(
            select(BatchCompletion)
            .where(BatchCompletion.job_id == job_id)
            .order_by(BatchCompletion.completed_at, BatchCompletion.attempt)
        )
    )


def ensure_job(
    session: Session,
    job_id: str,
    run_date: str,
    portfolio_id: str,
    transaction_count: int = 0,
    total_amount: str | Decimal = "0.00",
    fault_injection: str | None = None,
) -> BatchJob:
    job = session.get(BatchJob, job_id)
    if job is None:
        job = BatchJob(
            job_id=job_id,
            run_date=run_date,
            portfolio_id=portfolio_id,
            transaction_count=transaction_count,
            total_amount=str(Decimal(str(total_amount)).quantize(Decimal("0.01"))),
            fault_injection=fault_injection,
        )
        session.add(job)
        session.commit()
    return job


def delete_job(session: Session, job_id: str) -> None:
    for completion in completions_for_job(session, job_id):
        session.delete(completion)
    job = session.get(BatchJob, job_id)
    if job is not None:
        session.delete(job)
    session.commit()
