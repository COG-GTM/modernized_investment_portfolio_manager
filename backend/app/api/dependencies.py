"""
Shared FastAPI dependencies for database sessions, authentication, and pagination.

Replaces:
- DB2ONLN connection pool manager (connection acquisition/release)
- INQCOM.cpy communication area passing between CICS programs
- SECMGR user validation integrated into every CICS transaction
"""

import logging
from typing import Generator, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.middleware.auth import decode_access_token
from app.api.schemas import UserInfo

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OAuth2 scheme — replaces CICS ASSIGN USERID
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ---------------------------------------------------------------------------
# Database session dependency — replaces DB2ONLN connection pool
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session from the connection pool.

    Replaces DB2ONLN P100-PROCESS-CONNECT / P200-PROCESS-DISCONNECT:
    - COBOL: EXEC SQL CONNECT TO POSMVP -> session from pool
    - COBOL: EXEC SQL DISCONNECT -> session.close()
    - Pool limits enforced by SQLAlchemy engine (pool_size, max_overflow)
      replacing WS-MAX-CONNECTIONS PIC S9(8) COMP VALUE 100.
    """
    from models import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Auth dependency — replaces SECMGR validation + authorization
# ---------------------------------------------------------------------------

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> UserInfo:
    """
    Validate JWT token and return current user info.

    Replaces the SECMGR three-step security check from INQONLN P050-SECURITY-CHECK:
      1. SEC-VALIDATE ('V') — Validate user credentials -> JWT decode
      2. SEC-AUTHORIZE ('A') — Check resource access    -> role check
      3. SEC-AUDIT ('L')     — Log access               -> logging below

    COBOL flow:
      EXEC CICS ASSIGN USERID(SEC-USER-ID)
      EXEC CICS LINK PROGRAM('SECMGR') COMMAREA(WS-SECURITY-REQUEST)
      IF SEC-RESPONSE-CODE NOT = 0 -> HTTPException 401
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserInfo(
        user_id=payload.get("sub", ""),
        roles=payload.get("roles", []),
    )

    # Audit logging — replaces SECMGR P300-LOG-ACCESS
    logger.info("Access by user=%s roles=%s", user.user_id, user.roles)

    return user


def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[UserInfo]:
    """Optional auth — allows unauthenticated access (for health checks, etc.)."""
    if token is None:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    return UserInfo(
        user_id=payload.get("sub", ""),
        roles=payload.get("roles", []),
    )


# ---------------------------------------------------------------------------
# Pagination parameters — replaces CURSMGR array fetch sizing
# ---------------------------------------------------------------------------

class PaginationParams:
    """
    Pagination query parameters.

    Replaces CURSMGR WS-MAX-ROWS (PIC S9(4) COMP VALUE 20) and the
    INQHIST cursor-based scrolling (PF7=Previous, PF8=Next).
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-based)"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
        cursor: Optional[str] = Query(None, description="Cursor for cursor-based pagination"),
    ):
        self.page = page
        self.per_page = per_page
        self.cursor = cursor
        self.offset = (page - 1) * per_page
