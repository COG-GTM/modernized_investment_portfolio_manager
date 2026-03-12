from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from routers import portfolio, accounts

# New CICS-migrated API modules
from app.api.middleware.error_handler import register_exception_handlers
from app.api.routes import health as api_health, history as api_history, portfolio as api_portfolio
from app.api.routes.auth import router as api_auth_router

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

# Register global error handlers (migrated from ERRHNDL.cbl)
register_exception_handlers(app)

# Existing routers
app.include_router(portfolio.router)
app.include_router(accounts.router)

# New CICS-migrated API routers (under /api/v1/)
app.include_router(api_auth_router)
app.include_router(api_portfolio.router)
app.include_router(api_history.router)
app.include_router(api_health.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
