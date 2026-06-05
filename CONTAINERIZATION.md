# Containerization

This repo is containerized as two images orchestrated with Docker Compose:

| Service    | Image base            | Role                                                        | Port |
|------------|-----------------------|-------------------------------------------------------------|------|
| `backend`  | `python:3.12-slim`    | FastAPI API; runs Alembic migrations + seed on startup      | 8000 |
| `frontend` | `nginx:1.27-alpine`   | React/Vite static build served by nginx; proxies `/api`     | 8080 |

## Quick start

```bash
docker compose up --build
# open http://localhost:8080   (UI)
# open http://localhost:8000/docs  (API docs)
```

The frontend calls `/api/...` on its own origin; nginx proxies those requests to
`backend:8000` (see `nginx.conf`), so no CORS or hardcoded host is needed in the
browser bundle.

## How it maps to the containerization lifecycle

### 1. Assess
- Backend: Python 3.12 + Poetry (`backend/pyproject.toml`), FastAPI, SQLAlchemy,
  Alembic migrations, SQLite database, seed script.
- Frontend: Node 20 + Vite + React, builds to static assets in `dist/`.

### 2. Author (multi-stage Dockerfiles)
- `backend/Dockerfile`: builder stage installs runtime deps into an in-project
  virtualenv with Poetry; slim runtime stage copies only the venv + source, runs
  as a non-root user (`appuser`, uid 10001).
- `Dockerfile` (frontend): Node builder stage runs `npm ci && npm run build`;
  nginx runtime stage serves the static output. Final image is ~50 MB.
- `.dockerignore` files keep build contexts small (no `node_modules`, `.venv`,
  `.git`, local DBs).

### 3. Externalize config (12-factor)
Two small, backward-compatible code changes make the app container-friendly:
- `backend/models/database.py` + `backend/migrations/env.py` read `DATABASE_URL`
  from the environment (default stays SQLite for local dev).
- `src/services/api.ts` reads `VITE_API_BASE_URL` (default stays
  `http://localhost:8000/api` for local dev). The container build sets it to
  `/api` so the browser talks to the same origin.

### 4. Build, run, verify
Both images build clean and the stack runs end-to-end:
- `GET /healthz` → `{"status":"ok"}`
- `GET /api/portfolio/1234567890` returns seeded portfolio data (direct and via
  the nginx proxy on :8080).
- Backend container `HEALTHCHECK` gates the frontend via `depends_on:
  service_healthy`.

Database state persists in the `backend-data` named volume.

### 5. Optimize & harden
- Multi-stage builds keep build tools (Poetry, Node) out of the runtime images.
- Non-root runtime user in the backend.
- Backend `HEALTHCHECK` uses a Python one-liner instead of installing `curl` —
  this removed ~14 MB and eliminated all the OS-package CVEs that the `curl`
  layer had introduced (verified by re-scanning with Snyk).

## Security scan results (Snyk)

Run via Snyk MCP (`snyk_container_scan`). Excluding base-image CVEs (which are
remediated by bumping the base image tag in CI):

- **Frontend image app layers:** no vulnerable paths found.
- **Backend image OS layers:** no vulnerable paths found (after dropping `curl`).
- **Backend application dependencies (SCA):** 15 issues in transitive Python
  packages, each with a pinned-upgrade fix, e.g.:
  - `starlette` → ReDoS / request smuggling (High/Med)
  - `python-multipart` → directory traversal / DoS (High)
  - `mako` (via Alembic) → directory traversal (High)
  - `urllib3`, `idna`, `click`, `pygments`, `python-dotenv` → various
  - Note: several come through `fastapi[standard]` → `fastapi-cli` →
    `fastapi-cloud-cli`, which is not needed at runtime; dropping that extra
    removes a whole cluster of findings.

These dependency upgrades are intentionally **not** bundled into this
containerization PR to keep it focused; they are a good follow-up (e.g. via an
automated security-remediation pass).

## Known limitation: Postgres requires a schema change

A Postgres service is included (commented out) in `docker-compose.yml`. The app
currently targets SQLite: `positions.portfolio_id` has a foreign key to
`portfolios(port_id)`, but that table's primary key is the composite
`(port_id, account_no)`. SQLite tolerates this; **Postgres rejects it**
(`there is no unique constraint matching given keys for referenced table`).

Moving to Postgres therefore requires an app-level data-model decision (make
`port_id` unique, or reference the full composite key) and a migration. That is
left to the team rather than silently changing the schema here.

## CI

`.github/workflows/docker.yml` builds both images on every PR, scans them with
Trivy (results uploaded to the GitHub Security tab), and pushes to GHCR on
pushes to `main` and version tags.
