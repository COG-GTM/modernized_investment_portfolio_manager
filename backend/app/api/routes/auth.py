"""
Authentication endpoints — replaces SECMGR.cbl login flow.

COBOL SECMGR SEC-VALIDATE ('V'):
  EXEC CICS ASSIGN USERID(WS-USER-ID)
  Compare SEC-USER-ID with WS-USER-ID
  SEC-RESPONSE-CODE = 0 (success) or 8 (failure)

This endpoint issues JWT tokens instead of relying on CICS session auth.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status

from app.api.middleware.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
)
from app.api.schemas import LoginRequest, TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user",
    description=(
        "Authenticate user credentials and return a JWT token. "
        "Replaces SECMGR SEC-VALIDATE ('V') CICS user validation."
    ),
)
async def login(request: LoginRequest) -> TokenResponse:
    """
    User login — replaces SECMGR P100-VALIDATE-USER.

    COBOL equivalent:
      MOVE 'V' TO SEC-REQUEST-TYPE
      EXEC CICS ASSIGN USERID(WS-USER-ID)
      IF SEC-USER-ID = WS-USER-ID -> SEC-RESPONSE-CODE = 0
      ELSE -> 'User validation failed', SEC-RESPONSE-CODE = 8

    On success, also performs authorization check and audit log
    (replaces SECMGR P200-CHECK-AUTH and P300-LOG-ACCESS).
    """
    user_data = authenticate_user(request.username, request.password)

    if user_data is None:
        # Replaces SECMGR: SEC-RESPONSE-CODE = 8, 'User validation failed'
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token — replaces CICS session establishment
    token = create_access_token(
        user_id=user_data["user_id"],
        roles=user_data["roles"],
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user_data["user_id"],
        roles=user_data["roles"],
    )
