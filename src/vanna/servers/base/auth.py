"""Authentication helpers for local and secured server deployments."""

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException


@dataclass(frozen=True)
class AuthenticatedUser:
    """Authenticated identity and administrative capability."""

    user_id: str
    is_admin: bool


def authenticate_request(
    request: Any, config: Dict[str, Any]
) -> AuthenticatedUser:
    """Resolve a signed session when authentication is enabled."""
    if not config.get("require_auth", False):
        return AuthenticatedUser(user_id="demo-user", is_admin=True)

    secret = str(config.get("auth_secret") or os.getenv("VANNA_AUTH_SECRET") or "")
    if len(secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured for this server",
        )

    session = request.cookies.get("vanna_session")
    if not session:
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            session = authorization[7:].strip()
    identity = verify_session(session, secret)
    if identity is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    admin_email = str(
        config.get("admin_email") or os.getenv("VANNA_ADMIN_EMAIL") or ""
    ).casefold()
    return AuthenticatedUser(
        user_id=identity,
        is_admin=bool(admin_email and identity.casefold() == admin_email),
    )


def sign_session(user_id: str, secret: str) -> str:
    """Create a signed session token for trusted authentication middleware."""
    payload = user_id.strip()
    if not payload or len(secret) < 32:
        raise ValueError("A user ID and 32-character authentication secret are required")
    signature = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{signature}"


def verify_session(session: Optional[str], secret: str) -> Optional[str]:
    """Verify a signed session token without exposing signature details."""
    if not session or "." not in session:
        return None
    user_id, signature = session.rsplit(".", 1)
    expected = hmac.new(
        secret.encode("utf-8"), user_id.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    return user_id or None
