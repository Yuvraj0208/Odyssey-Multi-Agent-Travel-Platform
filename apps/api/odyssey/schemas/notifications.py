"""Proactive notification contract (surfaced as toasts + an inbox in the UI)."""

from __future__ import annotations

import time
import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


class NotificationKind(StrEnum):
    weather = "weather"
    price = "price"
    availability = "availability"
    info = "info"


class Notification(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    kind: NotificationKind = NotificationKind.info
    severity: str = "info"  # info | warning
    title: str
    body: str
    session_id: str | None = None
    # A ready-to-send chat prompt that asks the agents to act on this (one-click re-plan).
    suggested_prompt: str | None = None
    created_at: float = Field(default_factory=lambda: time.time())
    read: bool = False
