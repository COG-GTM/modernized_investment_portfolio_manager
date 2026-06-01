"""
Health check endpoint — replaces DB2ONLN.cbl P300-CHECK-STATUS.

COBOL DB2ONLN status check:
  EXEC SQL SELECT CURRENT SERVER INTO :DB2-ERROR-MSG END-EXEC
  IF SQLCODE = 0 -> DB2-RESPONSE-CODE = 0 (healthy)
  ELSE           -> DB2-RESPONSE-CODE = -1 (unhealthy)

  Also returns WS-ACTIVE-CONNECTIONS count.

This endpoint verifies:
  1. API is responsive
  2. Database connection is healthy (via a simple query)
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_optional_user
from app.api.schemas import HealthCheckResponse, UserInfo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/api/v1/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description=(
        "Check API and database health status. "
        "Replaces DB2ONLN P300-CHECK-STATUS (SELECT CURRENT SERVER)."
    ),
)
async def health_check(
    db: Session = Depends(get_db),
) -> HealthCheckResponse:
    """
    Health check — replaces DB2ONLN P300-CHECK-STATUS:
      EXEC SQL SELECT CURRENT SERVER INTO :DB2-ERROR-MSG END-EXEC
      IF SQLCODE = 0 -> healthy
    """
    db_status = "ok"
    try:
        # Replaces: EXEC SQL SELECT CURRENT SERVER INTO :DB2-ERROR-MSG
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_status = "error"

    overall_status = "ok" if db_status == "ok" else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        database=db_status,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
