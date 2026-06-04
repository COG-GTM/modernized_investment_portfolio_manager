import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from routers import portfolio, accounts

# Default to the local frontend origin (Vite dev server). Override in
# production via the ALLOWED_ORIGINS env var (comma-separated list).
DEFAULT_ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:5173"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
]

# OpenAPI docs are enabled by default for local dev. Set ENABLE_DOCS=false
# (e.g. in production) to disable /docs, /redoc, and /openapi.json.
docs_enabled = os.getenv("ENABLE_DOCS", "true").lower() in ("true", "1", "yes")

app = FastAPI(
    title="Portfolio Management API",
    description="FastAPI backend service for investment portfolio management",
    version="1.0.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

# Restrict CORS to an explicit allowlist. Never combine "*" with
# allow_credentials=True, which would let any origin make credentialed requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio.router)
app.include_router(accounts.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
