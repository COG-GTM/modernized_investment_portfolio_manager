# Batch-completion service scenario (synthetic demonstration)

A durable batch-completion step for the modernized portfolio system: end-of-day
transaction-posting jobs (one per portfolio / run date) are executed by a worker and, when
done, a completion record is written through `POST /batch/jobs/{job_id}/complete`.

**Invariant:** exactly one completion record per logical job, including after client
retries and service restarts.

Everything here is synthetic. No real portfolios, ledgers or downstream systems are touched.

## Layout

| Path | Purpose |
| --- | --- |
| `models.py`, `migrations/versions/7c1e2d3f4a5b_*` | `batch_jobs` and `batch_completions` tables (Alembic) |
| `service.py` | Completion logic + fault injector (`pre_ack_stall_ms`) |
| `router.py` | FastAPI router mounted on the main app under `/batch` |
| `client.py` | Client with a bounded retry policy on timeout (fresh request id per attempt) |
| `worker.py` | Worker/CLI that runs jobs and posts completions |
| `replay.py` | Request-replay tool: reproduces the client retry sequence and emits a trace |
| `check_retry_safety.py` | Independent validation check (`check-retry-safety`) |
| `seed.py` | Seed / reset of this scenario's own rows only |
| `../tests/techfest_batch/` | pytest unit + integration coverage (part of the default test command) |
| `TASK_PROMPT.md` | Copy/paste prompt for the remediation session |
| `ANSWER_KEY.md` | **Presenter-only.** Not referenced by the prompt. |

The UI page is `src/pages/BatchCompletions.tsx` (Main Menu option 3, route
`/batch-completions`). Every badge on it reads real service state (`/batch/status`,
`/batch/jobs`); saved (rehearsal) results and live runs are shown in separate panels.

## Scenario refs

| Ref | Meaning |
| --- | --- |
| `techfest/batch/baseline` | `TECHFEST_BATCH_SCENARIO` unset or `baseline`: fault injector off |
| `techfest/batch/broken` | `TECHFEST_BATCH_SCENARIO=broken`: the service persists the completion and then stalls (`TECHFEST_BATCH_STALL_MS`, default 1500 ms) before acknowledging the **first** attempt of any job flagged `fault_injection=PRE_ACK_STALL` (seeded: `EOD-POST-PORT0002-20240628`). The client timeout is 1.0 s, so the client retries. |

The scenario is selected by environment variable, not by a git ref; the same code revision
serves both. The **starting revision** (the commit on the setup branch that carries the broken
scenario) is recorded in the setup PR description. Code revision = `git rev-parse HEAD` at
service start (`TECHFEST_CODE_REVISION` overrides it).

## Commands (run from `backend/`, venv active)

```bash
# schema + seed
alembic upgrade head
python -m techfest_batch seed

# start the stack (baseline)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
npm run dev                          # from the repo root; page at http://localhost:3000/batch-completions

# select the broken scenario ref
export TECHFEST_BATCH_SCENARIO=broken
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# run a job through the worker/client
python -m techfest_batch run --job EOD-POST-PORT0001-20240628

# reproduce the duplicate (broken ref) and emit the trace (table + JSON); exit 1 on duplicate
TECHFEST_BATCH_SCENARIO=broken python -m techfest_batch.replay --job EOD-POST-PORT0002-20240628
TECHFEST_BATCH_SCENARIO=broken python -m techfest_batch.replay --job EOD-POST-PORT0002-20240628 --restart --json

# independent validation check (NOT part of the default test command); exit 1 on FAIL
./techfest_batch/techfest-batch check-retry-safety
TECHFEST_BATCH_SCENARIO=broken ./techfest_batch/techfest-batch check-retry-safety

# default test command (stays green apart from the repo's pre-existing intentional IDOR failures)
python -m pytest tests/ -v

# restore starting state (removes only EOD-POST-*/CHECK-* jobs, their completions and saved traces)
python -m techfest_batch reset
python -m techfest_batch seed
```

`--server-url http://localhost:8000` on `run`/`replay` targets a running service instead of the
ephemeral in-process one; both use the same SQLite file (`backend/portfolio.db`, override with
`TECHFEST_BATCH_DATABASE_URL`).

## What the check covers

`check-retry-safety` drives the service over HTTP against the persistent SQLite store:
distinct jobs, replay of an identical request, client timeout + bounded retry with the fault
injector armed on the probe job, and a resend across a service restart (new server, same file).
It writes `data/last_check.json`, which the page displays as the saved result.

The default pytest suite covers single-attempt cases and distinct jobs only; it does not
exercise the retry path. Concurrent same-job requests are not covered by the check either —
that coverage is expected from the regression test the remediation adds.

## Reset

`python -m techfest_batch reset` deletes only rows whose `job_id` starts with `EOD-POST-` or
`CHECK-` and the two saved JSON traces under `data/`. Portfolio, position, transaction and
history tables are untouched. Nothing rewrites git history; the starting revision remains
reachable on the setup branch.
