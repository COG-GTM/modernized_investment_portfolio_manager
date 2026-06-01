from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from routers import portfolio, accounts

# New CICS-migrated API sub-application (scoped to /api/v1/)
from app.api.main import create_api_app

app = FastAPI(
    title="Portfolio Management API",
    description="FastAPI backend service for investment portfolio management",
    version="1.0.0"
)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Existing routers (unchanged — keep default FastAPI error format)
app.include_router(portfolio.router)
app.include_router(accounts.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Mount the CICS-migrated API as a sub-application so its custom error
# handlers (ERRHNDL) are scoped only to /api/v1/ routes and do not
# change the error response format for pre-existing endpoints.
# NOTE: This must come AFTER all main-app route definitions because
# mount("/") matches all paths — any routes defined after it would be
# unreachable (the mount intercepts the request first).
api_v1_app = create_api_app()
app.mount("/", api_v1_app)
