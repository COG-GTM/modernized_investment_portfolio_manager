# Remediation Report — Hunter Pipeline (Stage 5: Fix & Verify)

**Repository:** COG-GTM/modernized_investment_portfolio_manager
**Scope:** Defensive remediation of confirmed (Stage 4 dynamic-validated) findings DF-02 → DF-06, plus a judgment call on DF-01.
**Approach:** Minimal, env-var-configurable fixes. Safe-by-default, dev still works. No tests modified.

## Test command & results (before → after)

Command:
```bash
cd backend && source .venv/bin/activate && python -m pytest tests/ -v
```

| | Result |
|---|---|
| **Before** | `10 failed, 36 passed` |
| **After** | `46 passed` |

The 10 pre-existing failures were all in `TestValidateAccountNumber`. They encode the **real** validation contract (rejecting malformed account numbers) and were failing only because validation was stubbed to bypass. They do **not** assert the vulnerability, so fixing the code (not the tests) made them pass — no STOP condition was triggered.

Frontend build:
```bash
npm run build   # tsc && vite build  →  passed (155 modules, built in ~1s)
```
Backend: no linter configured in `pyproject.toml`; `python -m py_compile` clean on all changed files.

---

## Findings fixed

### DF-05 — Wildcard CORS + credentials  (`backend/app/main.py`)
- **Before:** `allow_origins=["*"]` combined with `allow_credentials=True`. Starlette reflects the request `Origin` in this configuration, so any site could make credentialed cross-origin requests.
- **After:** Origins restricted to an explicit allowlist read from env var `ALLOWED_ORIGINS` (comma-separated), defaulting to the local frontend origins `http://localhost:3000,http://localhost:5173`. `"*"` is never combined with credentials.
- **Verified:** `Origin: http://evil.com` → no `Access-Control-Allow-Origin` header; `Origin: http://localhost:3000` → reflected. `ALLOWED_ORIGINS=https://app.example.com` honored at startup.
- Ref: `backend/app/main.py:8-15`, `:30-38`.

### DF-04 — `validate_account_number()` stubbed to always return True  (`backend/validation/portfolio.py`)
- **Before:** `return True, "Validation bypassed"` for any input.
- **After:** Real validation per the repo's domain rules and existing tests: exactly 10 characters, numeric only, not all zeros. Returns the specific failure messages the test suite expects (`"Account number must be exactly 10 digits"`, `"Account number must contain only numeric characters"`, `"Account number cannot be all zeros"`, `"Valid account number"`). Check ordering matches the tests (empty→length msg, non-numeric→numeric msg, wrong length→length msg, all-zeros→zeros msg).
- **Verified:** All `TestValidateAccountNumber` + `TestEdgeCases` cases pass.
- Ref: `backend/validation/portfolio.py:19-33`.

### DF-02 / DF-03 — IDOR: account validation commented out  (`backend/routers/portfolio.py`)
- **Before:** Both `GET /api/portfolio/{account_number}` and `GET /api/transactions/{account_number}` had the validation block commented out under `# Removed account validation - IDOR vulnerability`, accepting any account string.
- **After:** Server-side validation re-enabled on both routes via the now-real `validate_account_number`; malformed account numbers return `400` with the validation message. This removes the IDOR root cause (no input validation) before the routes are wired to real data.
- **Verified:** `/api/portfolio/1234567890` → 200; `/api/portfolio/123`, `/api/portfolio/0000000000`, `/api/transactions/abc` → 400.
- Ref: `backend/routers/portfolio.py:62-69`, `:72-82`.

> Note: data is still mock today, so this is a defensive hardening of the input boundary. True object-level authorization (does *this user* own *this account*) requires DF-01 (auth) — see below.

### DF-06 — Unauthenticated OpenAPI docs/schema  (`backend/app/main.py`)
- **Before:** `/docs`, `/redoc`, `/openapi.json` always exposed.
- **After:** Docs gated behind env flag `ENABLE_DOCS` (default `true` to preserve the dev workflow). Set `ENABLE_DOCS=false` in production to set `docs_url`/`redoc_url`/`openapi_url` to `None`.
- **Decision:** Kept enabled by default for dev; production-disable is a one-env-var change. This avoids breaking the local developer experience while making the prod-safe configuration trivial.
- **Verified:** default → `/docs` 200, `/openapi.json` 200; `ENABLE_DOCS=false` → both 404.
- Ref: `backend/app/main.py:17-19`, `:25-27`.

---

## DF-01 — No authentication layer (judgment call: scaffold added, full impl deferred)

A full auth system is a large architectural change that doesn't fit the app's current mock-data state and risks regressing the suite. Rather than bolt on a half-baked system, I added a **clean, non-enforcing, pluggable hook** and documented the full implementation as follow-up.

**What was added (`backend/app/auth.py`):** a `get_current_user` FastAPI dependency, wired into the two portfolio data routes via `Depends(get_current_user)` (`backend/routers/portfolio.py:63`, `:73`).
- Default (`REQUIRE_AUTH` unset/false): returns an anonymous principal and never blocks — **zero behavior change** for dev and the existing tests (which only exercise the validation layer; all 46 still pass).
- `REQUIRE_AUTH=true`: enforces presence of an `Authorization: Bearer <token>` header, returning `401` when missing/malformed.
- **Verified:** `REQUIRE_AUTH=true` → no header = 401, `Bearer abc` = 200; default mode unchanged.

**Why not full auth now:** token issuance/verification (JWT/OAuth), a user store, and per-user → account ownership mapping are out of scope for a surgical security PR and would require product decisions (identity provider, session model). The scaffold gives a single, obvious wiring point.

**Concrete follow-up plan for DF-01:**
1. Choose an IdP / token format (e.g. OIDC JWT) and add verification in `auth.py::get_current_user` (replace the `TODO(DF-01)` — verify signature/expiry, load user).
2. Introduce a user↔account ownership model and enforce object-level authorization inside the portfolio/transactions routes (the real IDOR defense once data is non-mock).
3. Flip `REQUIRE_AUTH=true` in non-dev environments and add route-level integration tests for 401/403 paths.

---

## Configuration summary (safe defaults, dev-friendly)

| Env var | Default | Production recommendation |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | explicit prod frontend origin(s) |
| `ENABLE_DOCS` | `true` | `false` |
| `REQUIRE_AUTH` | `false` | `true` (after DF-01 full impl) |

## Files changed
- `backend/app/main.py` — DF-05 (CORS allowlist), DF-06 (docs toggle)
- `backend/validation/portfolio.py` — DF-04 (real account-number validation)
- `backend/routers/portfolio.py` — DF-02/03 (re-enable validation), DF-01 (wire auth hook)
- `backend/app/auth.py` — DF-01 (pluggable auth scaffold, new file)
