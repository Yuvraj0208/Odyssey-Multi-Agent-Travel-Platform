"""Chat + session request/response contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class ResumeIn(BaseModel):
    """User's decision on a human-in-the-loop approval."""

    approved: bool
    booking_id: str | None = None
    note: str | None = None


class SessionOut(BaseModel):
    session_id: str
    user_id: str
    status: str = "active"
    title: str | None = None
