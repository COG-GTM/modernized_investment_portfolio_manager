Repo: COG-GTM/modernized_investment_portfolio_manager
Work from branch `devin/1790129830-techfest-batch` (pull it first; do not branch from main). Open your PR against that branch, not against main.

CONTEXT
The retry-safety validation check for the batch-completion service is failing at revision 0f1a1d1a19dd22ccb718755639f0bb06f4c2eada on branch `devin/1790129830-techfest-batch`. The service lives in `backend/techfest_batch/` (FastAPI + SQLAlchemy + Alembic on SQLite, `backend/portfolio.db`); read `backend/techfest_batch/README.md` and `backend/README.md` for setup and commands. Its invariant is: exactly one completion record per logical batch job, including after client retries and service restarts. Endpoint: `POST /batch/jobs/{job_id}/complete`.

OBSERVED SYMPTOMS
- `cd backend && TECHFEST_BATCH_SCENARIO=broken ./techfest_batch/techfest-batch check-retry-safety` reports `timeout_then_retry_yields_single_completion: FAIL` (2 completion records for one logical job). The other probes pass. Without the env var the check passes.
- `cd backend && TECHFEST_BATCH_SCENARIO=broken python -m techfest_batch.replay --job EOD-POST-PORT0002-20240628` reproduces it every time: attempt 1 times out at the client, attempt 2 returns 200, and two `batch_completions` rows exist for the job with different completion ids. The trace (JSON + table) shows request ids, attempt numbers, timestamps, response codes and code revision per attempt.
- The default suite `python -m pytest tests/techfest_batch -q` passes on this revision; it does not exercise the retry path.

TASK
1. Investigate the failure and reproduce the duplicate with the provided replay tooling.
2. Add a meaningful regression test under `backend/tests/techfest_batch/` that FAILS on the current code and PASSES after your fix. Keep it in the default pytest path so it runs in recurring CI; do not add it to the seeded-failure command.
3. Repair the underlying idempotency behavior of the completion endpoint.
4. Return a bounded PR against `devin/1790129830-techfest-batch` with verification.

ACCEPTANCE (all must be shown in the PR)
- The same regression test fails on the unrepaired code and passes on the repaired code — include both runs' output.
- Repeated and concurrent requests for the same logical job yield exactly one persisted completion and return the same completion identity.
- A distinct job still creates its own completion record.
- Restarting the service (new process, same SQLite file) does not defeat deduplication.
- Tests exercise the persistent-storage behavior (SQLite through SQLAlchemy), not an in-memory cache.
- `TECHFEST_BATCH_SCENARIO=broken ./techfest_batch/techfest-batch check-retry-safety` reports PASS on your head; include the output.
- The PR description contains: diagnosis, reproduction commands, before/after results, and an explicit statement of coverage limits for external side effects (e.g. downstream notifications, ledger postings) that the tests do not cover.

FORBIDDEN
- Disabling, shortening or reducing client retries or lengthening the client timeout.
- Deleting duplicate evidence (existing rows, traces, the replay tool or the fault injector).
- Weakening or removing assertions in existing tests or in `check_retry_safety.py`.
- Changing the client contract (request shape, a fresh request id per attempt, response shape) or the storage engine (SQLite via SQLAlchemy/Alembic).
- Changes outside `backend/techfest_batch/`, its migration under `backend/migrations/versions/`, and `backend/tests/techfest_batch/`, except the minimum needed.

ESCALATION
If the fix would require changing the storage engine or the client contract, stop and report instead of proceeding.

CONVENTIONS
Commit messages must contain the word "feature" or "bug". Customer-neutral wording only; synthetic data only. Do not merge. End your PR description with this exact line on its own:
Devin-Org: engineering
