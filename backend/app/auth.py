"""Pluggable authentication scaffold (DF-01).

This module provides a single dependency, ``get_current_user``, that route
handlers can depend on so a real authentication layer can be wired up later
without touching every endpoint.

Default behaviour is intentionally NON-enforcing so the current mock-data dev
workflow (and the existing test suite) keep working unchanged: requests are
treated as an anonymous principal. Set ``REQUIRE_AUTH=true`` to turn on a
minimal bearer-token presence check that returns 401 when the header is
missing/malformed.

This is a scaffold, NOT a complete auth system. Replace ``_resolve_principal``
with real token verification (e.g. JWT/OAuth introspection) and a user store
when an identity provider is available. See remediation-report.md (DF-01).
"""
import os
from typing import Optional

from fastapi import Header, HTTPException


def _auth_required() -> bool:
    return os.getenv("REQUIRE_AUTH", "false").lower() in ("true", "1", "yes")


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """FastAPI dependency that resolves the current principal.

    - When ``REQUIRE_AUTH`` is unset/false: returns an anonymous principal and
      never blocks (preserves current dev/test behaviour).
    - When ``REQUIRE_AUTH`` is true: requires a ``Authorization: Bearer <token>``
      header and rejects the request with 401 if it is missing/malformed.

    NOTE: This does not yet *verify* the token. Token verification must be
    implemented before relying on this for real access control.
    """
    if not _auth_required():
        return {"sub": "anonymous", "authenticated": False}

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO(DF-01): verify token signature/expiry and load the real user record.
    return {"sub": token, "authenticated": True}
