"""Shared API dependencies.

current_user is a seam: in Phase 1 (dev) it reads an x-user-id header or falls back
to a demo user, so the frontend works end to end without auth. Phase 5 swaps the
body for real JWT verification without touching the routers.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header


@dataclass
class CurrentUser:
    id: str
    email: str | None = None


async def current_user(x_user_id: str | None = Header(default=None)) -> CurrentUser:
    return CurrentUser(id=x_user_id or "demo-user", email=None)
