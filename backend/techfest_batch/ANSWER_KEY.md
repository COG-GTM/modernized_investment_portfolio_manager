# ANSWER KEY — presenter only

Do not share with, or reference from, the remediation session.

## Root cause

`service.complete_job` deduplicates on **`request_id` only**. The client (`client.py`)
generates a **fresh request id on every retry attempt**, so a retry after a timed-out first
attempt is treated as a new request. Nothing in the schema prevents two `batch_completions`
rows for the same `job_id` (only a non-unique index). The fault injector
(`pre_ack_stall_ms`, honored only when `TECHFEST_BATCH_SCENARIO=broken`) commits the
completion and then sleeps past the 1.0 s client timeout on attempt 1, so the client retries
and the service writes a second completion.

## Expected repair shape

- Idempotency keyed on the **logical job id** (request id may remain as a secondary key /
  audit field).
- A **unique constraint** on `batch_completions.job_id` via an Alembic migration (and the
  model), so the guarantee lives in storage and survives restarts and concurrency.
- Insert-first, catch `IntegrityError` (or `INSERT ... ON CONFLICT` / `SELECT ... FOR UPDATE`
  equivalent for SQLite), then return the **existing** completion with `deduplicated=true`,
  same `completion_id`.
- Regression test that arms the fault injector (or calls the service twice with distinct
  request ids for the same job, including from threads) and asserts one persisted row and a
  stable completion identity; test runs against a SQLite file through SQLAlchemy, and a
  fresh engine/session ("restart") still sees the dedup.
- Add the regression test to the default pytest path (tests/techfest_batch/) so it runs in CI;
  `check-retry-safety` stays a separate command.

## Anti-patterns to reject in review

- Reusing the request id across retries (changes the client contract; forbidden).
- Lengthening the client timeout / reducing retries (forbidden).
- In-memory "seen jobs" set or lock in the process (defeated by restart and multi-worker).
- Deleting the duplicate rows the replay produced (deleting evidence; forbidden).
- Removing the stall / fault injector.

## Verification presenter runs on the remediation PR head

```bash
cd backend && source .venv/bin/activate
alembic upgrade head
python -m pytest tests/ -q
TECHFEST_BATCH_SCENARIO=broken ./techfest_batch/techfest-batch check-retry-safety   # expect PASS
TECHFEST_BATCH_SCENARIO=broken python -m techfest_batch.replay --job EOD-POST-PORT0002-20240628  # expect 1 completion, same id on attempt 2 (deduplicated=true)
```
