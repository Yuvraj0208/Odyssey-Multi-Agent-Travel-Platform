"""Shared API dependencies.

current_user resolves the caller from a JWT (Authorization: Bearer ...). When
AUTH_REQUIRED is false (local demo default) it falls back to an x-user-id header so
the app works without login; when true, a valid token is mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException

from odyssey.core.config import get_settings
from odyssey.core.security import decode_access_token


@dataclass
class CurrentUser:
    id: str
    email: str | None = None
    name: str | None = None


async def current_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> CurrentUser:
    s = get_settings()

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            return CurrentUser(id=payload["sub"], email=payload.get("email"), name=None)
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    if s.auth_required:
        raise HTTPException(status_code=401, detail="Authentication required.")

    return CurrentUser(id=x_user_id or "demo-user", email=None)
