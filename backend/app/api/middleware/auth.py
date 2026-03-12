"""
JWT Authentication middleware — replaces SECMGR.cbl (Security Manager).

COBOL SECMGR performed three operations via SECURITY-REQUEST-AREA:
  1. SEC-VALIDATE ('V') — Validate CICS user credentials (EXEC CICS ASSIGN USERID)
  2. SEC-AUTHORIZE ('A') — Check DB2 AUTHFILE for resource/access permissions
  3. SEC-AUDIT ('L')     — Log access to DB2 AUDITLOG table

This module replaces all three with JWT-based authentication:
  - Login endpoint issues JWT tokens (replacing CICS session auth)
  - Token decode validates identity (replacing SEC-VALIDATE)
  - Role-based checks replace DB2 AUTHFILE lookups (replacing SEC-AUTHORIZE)
  - Python logging replaces AUDITLOG inserts (replacing SEC-AUDIT)

COBOL response codes mapped to HTTP status codes:
  SEC-RESPONSE-CODE = 0   -> 200 OK
  SEC-RESPONSE-CODE = 8   -> 401 Unauthorized ('User validation failed')
  SEC-RESPONSE-CODE = 12  -> 403 Forbidden ('Unable to obtain user credentials')
"""

import hashlib
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Secret key for JWT signing — MUST be set via environment variable.
# Falls back to a generated value for local development only.
_DEFAULT_DEV_KEY = hashlib.sha256(b"portfolio-inquiry-dev-only").hexdigest()
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", _DEFAULT_DEV_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))

# ---------------------------------------------------------------------------
# Demo user store — replaces SECMGR P100-VALIDATE-USER + DB2 AUTHFILE
# In production, this would query a real user database.
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def _load_demo_users() -> Dict[str, Dict]:
    """
    Load demo user store from environment or use defaults.
    In production, replace with a real user database query.
    """
    return {
        "admin": {
            "password_hash": os.environ.get(
                "DEMO_ADMIN_HASH",
                # default demo hash for local development
                _hash_password(os.environ.get("DEMO_ADMIN_PW", "admin")),
            ),
            "roles": ["admin", "portfolio_read", "portfolio_write", "history_read"],
            "full_name": "System Administrator",
        },
        "analyst": {
            "password_hash": os.environ.get(
                "DEMO_ANALYST_HASH",
                _hash_password(os.environ.get("DEMO_ANALYST_PW", "analyst")),
            ),
            "roles": ["portfolio_read", "history_read"],
            "full_name": "Portfolio Analyst",
        },
        "viewer": {
            "password_hash": os.environ.get(
                "DEMO_VIEWER_HASH",
                _hash_password(os.environ.get("DEMO_VIEWER_PW", "viewer")),
            ),
            "roles": ["portfolio_read"],
            "full_name": "Read-Only Viewer",
        },
    }


DEMO_USERS: Dict[str, Dict] = _load_demo_users()


# ---------------------------------------------------------------------------
# Token creation / verification
# ---------------------------------------------------------------------------

def create_access_token(user_id: str, roles: List[str], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Replaces SECMGR P100-VALIDATE-USER successful path where
    SEC-RESPONSE-CODE is set to 0 and the CICS session is established.
    """
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": user_id,
        "roles": roles,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info("Token created for user=%s roles=%s", user_id, roles)
    return token


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode and validate a JWT token.

    Replaces SECMGR P100-VALIDATE-USER where CICS ASSIGN USERID
    retrieves the current user and compares against SEC-USER-ID.
    Returns None on failure (equivalent to SEC-RESPONSE-CODE = 8).
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        logger.warning("Token decode failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# User authentication
# ---------------------------------------------------------------------------

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate user credentials against the user store.

    Replaces SECMGR P100-VALIDATE-USER:
      EXEC CICS ASSIGN USERID(WS-USER-ID)
      IF SEC-USER-ID = WS-USER-ID -> success
      ELSE -> 'User validation failed', SEC-RESPONSE-CODE = 8
    """
    user = DEMO_USERS.get(username)
    if user is None:
        logger.warning("Authentication failed: user '%s' not found", username)
        return None

    if user["password_hash"] != _hash_password(password):
        logger.warning("Authentication failed: bad password for user '%s'", username)
        return None

    # Audit logging — replaces SECMGR P300-LOG-ACCESS
    logger.info(
        "User authenticated: user=%s at=%s",
        username,
        datetime.now(timezone.utc).isoformat(),
    )
    return {"user_id": username, "roles": user["roles"], "full_name": user["full_name"]}


def check_authorization(roles: List[str], required_role: str) -> bool:
    """
    Check if user has the required role.

    Replaces SECMGR P200-CHECK-AUTH:
      EXEC SQL SELECT COUNT(*) FROM AUTHFILE
        WHERE USER_ID = :SEC-USER-ID
          AND RESOURCE = :SEC-RESOURCE-NAME
          AND ACCESS_TYPE = :SEC-ACCESS-TYPE
      If count > 0 -> SEC-RESPONSE-CODE = 0 (authorized)
      Else         -> SEC-RESPONSE-CODE = 8 ('Access denied')
    """
    return required_role in roles or "admin" in roles
