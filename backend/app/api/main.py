"""
FastAPI application entry point for the Portfolio Inquiry REST API.

Replaces INQONLN.cbl — the main CICS online inquiry handler that:
  - Managed CICS transaction PINQ (defined in PORTDFN.csd)
  - Received screen input via EXEC CICS RECEIVE MAP('INQMAP')
  - Dispatched to sub-programs based on INQCOM-FUNCTION:
      'MENU' -> P200-DISPLAY-MENU (now: frontend handles navigation)
      'INQP' -> P300-PORTFOLIO-INQUIRY -> LINK PROGRAM('INQPORT')
      'INQH' -> P400-HISTORY-INQUIRY  -> LINK PROGRAM('INQHIST')
      'EXIT' -> SESSION-TERMINATED
  - Called P050-SECURITY-CHECK -> LINK PROGRAM('SECMGR')
  - Called P900-ERROR-ROUTINE  -> LINK PROGRAM('ERRHNDL')

This module:
  - Creates the FastAPI app with CORS middleware
  - Registers all route handlers (portfolio, history, health, auth)
  - Registers global error handlers (replacing ERRHNDL)
  - Configures SQLAlchemy connection pooling (replacing DB2ONLN)
  - Sets up logging

Connection pool configuration replaces DB2ONLN.cbl:
  WS-MAX-CONNECTIONS PIC S9(8) COMP VALUE 100  -> pool_size + max_overflow
  WS-ACTIVE-CONNECTIONS tracking               -> SQLAlchemy pool status
  P110-ESTABLISH-CONNECTION                     -> pool auto-manages
  P200-PROCESS-DISCONNECT                      -> pool auto-manages
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.error_handler import register_exception_handlers
from app.api.routes import health, history, portfolio
from app.api.routes.auth import router as auth_router

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — replaces DB2ONLN connection establishment / cleanup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.

    Startup replaces DB2ONLN P100-PROCESS-CONNECT:
      EXEC SQL CONNECT TO POSMVP -> SQLAlchemy engine creates pool

    Shutdown replaces DB2ONLN P200-PROCESS-DISCONNECT:
      EXEC SQL DISCONNECT -> engine.dispose()
    """
    logger.info("Starting Portfolio Inquiry API (replacing CICS transaction PINQ)")
    logger.info(
        "Database pool configured: pool_size=%s, max_overflow=%s",
        os.environ.get("DB_POOL_SIZE", "5"),
        os.environ.get("DB_MAX_OVERFLOW", "10"),
    )
    yield
    logger.info("Shutting down Portfolio Inquiry API")
    # Engine disposal handled by SQLAlchemy / process exit


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_api_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Maps CICS resource definitions from PORTDFN.csd:
      DEFINE TRANSACTION(PINQ) PROGRAM(INQONLN)  -> This app
      DEFINE PROGRAM(INQPORT)  -> portfolio routes
      DEFINE PROGRAM(INQHIST)  -> history routes
      DEFINE PROGRAM(SECMGR)   -> auth middleware
      DEFINE PROGRAM(ERRHNDL)  -> error handlers
      DEFINE PROGRAM(DB2ONLN)  -> SQLAlchemy pool (startup)
      DEFINE PROGRAM(CURSMGR)  -> SQLAlchemy queries (in history routes)
      DEFINE PROGRAM(DB2RECV)  -> tenacity retry (in history routes)
      DEFINE MAPSET(INQSET)    -> JSON schemas
    """
    app = FastAPI(
        title="Portfolio Inquiry API",
        description=(
            "REST API for investment portfolio inquiries. "
            "Migrated from COBOL CICS online inquiry system "
            "(INQONLN/INQPORT/INQHIST/SECMGR/ERRHNDL/DB2ONLN/CURSMGR/DB2RECV)."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register error handlers — replaces ERRHNDL.cbl
    register_exception_handlers(app)

    # Register route handlers — replaces CICS LINK PROGRAM dispatching
    app.include_router(auth_router)         # SECMGR
    app.include_router(portfolio.router)    # INQPORT
    app.include_router(history.router)      # INQHIST + CURSMGR
    app.include_router(health.router)       # DB2ONLN status check

    return app
