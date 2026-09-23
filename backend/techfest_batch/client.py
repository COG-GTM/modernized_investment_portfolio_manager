"""Batch-completion client with a bounded retry policy on timeout.

Each attempt carries a fresh request id and its attempt number; every attempt is recorded
in a trace so the replay tool can show exactly what the service received.
"""
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import httpx

from techfest_batch.config import settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class AttemptRecord:
    attempt: int
    request_id: str
    started_at: str
    finished_at: str | None = None
    status_code: int | None = None
    outcome: str = "pending"  # ok | timeout | error
    completion_id: str | None = None
    deduplicated: bool | None = None
    code_revision: str | None = None
    error: str | None = None


@dataclass
class CompletionOutcome:
    job_id: str
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_completion_id: str | None = None
    exhausted: bool = False

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "attempts": [asdict(a) for a in self.attempts],
            "final_completion_id": self.final_completion_id,
            "exhausted": self.exhausted,
        }


class BatchCompletionClient:
    def __init__(
        self,
        base_url: str,
        timeout_s: float | None = None,
        max_attempts: int | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s if timeout_s is not None else settings.client_timeout_s
        self.max_attempts = max_attempts if max_attempts is not None else settings.client_max_attempts

    def complete_once(self, job_id: str, request_id: str, attempt: int) -> AttemptRecord:
        record = AttemptRecord(attempt=attempt, request_id=request_id, started_at=_now())
        try:
            with httpx.Client(timeout=self.timeout_s) as http:
                response = http.post(
                    f"{self.base_url}/batch/jobs/{job_id}/complete",
                    json={"request_id": request_id, "attempt": attempt},
                )
            record.status_code = response.status_code
            if response.status_code == 200:
                body = response.json()
                record.outcome = "ok"
                record.completion_id = body["completion_id"]
                record.deduplicated = body.get("deduplicated")
                record.code_revision = body.get("code_revision")
            else:
                record.outcome = "error"
                record.error = response.text[:200]
        except httpx.TimeoutException:
            record.outcome = "timeout"
            record.error = f"client timeout after {self.timeout_s}s"
        except httpx.HTTPError as exc:
            record.outcome = "error"
            record.error = repr(exc)
        record.finished_at = _now()
        return record

    def complete(self, job_id: str, on_attempt=None) -> CompletionOutcome:
        outcome = CompletionOutcome(job_id=job_id)
        for attempt in range(1, self.max_attempts + 1):
            record = self.complete_once(job_id, str(uuid.uuid4()), attempt)
            outcome.attempts.append(record)
            if on_attempt:
                on_attempt(record)
            if record.outcome == "ok":
                outcome.final_completion_id = record.completion_id
                return outcome
            if record.outcome == "error":
                return outcome
        outcome.exhausted = True
        return outcome
