"""Proactive notifications: live SSE stream + inbox history + mark-read.

The stream subscribes to the user's event-bus channel, so notifications produced by
the proactive coordinators (e.g. weather re-planning alerts) arrive without the user
asking - the event-driven half of the platform.
"""

from __future__ import annotations

import orjson
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from odyssey.api.deps import CurrentUser, current_user
from odyssey.core.events import ch_notify, get_event_bus
from odyssey.core.notifications import mark_read, recent_notifications

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
async def list_notifications(user: CurrentUser = Depends(current_user)) -> dict:
    return {"notifications": [n.model_dump(mode="json") for n in recent_notifications(user.id)]}


@router.post("/notifications/{note_id}/read")
async def read_notification(note_id: str, user: CurrentUser = Depends(current_user)) -> dict:
    mark_read(user.id, note_id)
    return {"ok": True}


@router.get("/notifications/stream")
async def notifications_stream(user: CurrentUser = Depends(current_user)):
    bus = get_event_bus()

    async def gen():
        # Replay unread history first so a reconnecting client is caught up.
        for n in reversed(recent_notifications(user.id)):
            if not n.read:
                yield {"event": "notification", "data": orjson.dumps(n.model_dump(mode="json")).decode()}
        async for payload in bus.subscribe(ch_notify(user.id)):
            yield {"event": "notification", "data": orjson.dumps(payload).decode()}

    return EventSourceResponse(gen(), ping=15000)
