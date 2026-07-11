"""Notification hub + the weather_changed -> notification coordinator.

Keeps a small per-user history (for the inbox) and publishes each notification on
the user's event-bus channel (for the live SSE toast stream). A background
coordinator subscribes to weather_changed events and turns them into proactive
notifications, closing the event-driven re-planning loop.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque

from odyssey.core.events import CH_WEATHER_CHANGED, ch_notify, get_event_bus
from odyssey.core.logging import get_logger
from odyssey.schemas.notifications import Notification, NotificationKind

log = get_logger(__name__)

# Per-user recent notifications (newest first), capped.
_HISTORY: dict[str, deque[Notification]] = defaultdict(lambda: deque(maxlen=50))


async def push_notification(user_id: str, note: Notification) -> None:
    _HISTORY[user_id].appendleft(note)
    await get_event_bus().publish(ch_notify(user_id), note.model_dump(mode="json"))
    log.info("notify.push", user_id=user_id, kind=str(note.kind), title=note.title)


def recent_notifications(user_id: str) -> list[Notification]:
    return list(_HISTORY[user_id])


def mark_read(user_id: str, note_id: str) -> None:
    for n in _HISTORY[user_id]:
        if n.id == note_id:
            n.read = True


async def _weather_coordinator() -> None:
    """Subscribe to weather_changed and emit a proactive notification per event."""
    bus = get_event_bus()
    try:
        async for payload in bus.subscribe(CH_WEATHER_CHANGED):
            user_id = payload.get("user_id")
            if not user_id:
                continue
            day = payload.get("day")
            date = payload.get("date")
            condition = payload.get("condition", "bad weather")
            items = payload.get("outdoor_items", [])
            item_hint = f" ({', '.join(items[:2])})" if items else ""
            note = Notification(
                kind=NotificationKind.weather,
                severity="warning",
                title=f"Weather alert for Day {day}",
                body=(
                    f"{condition.capitalize()} is now forecast for Day {day}"
                    f"{f' ({date})' if date else ''}, which affects outdoor plans{item_hint}. "
                    f"Want indoor alternatives?"
                ),
                session_id=payload.get("session_id"),
                suggested_prompt=(
                    f"The weather turned to {condition} on day {day}. Please swap the outdoor "
                    f"activities that day for good indoor alternatives and re-check the timing."
                ),
            )
            await push_notification(user_id, note)
    except asyncio.CancelledError:  # graceful shutdown
        raise
    except Exception as e:  # pragma: no cover
        log.warning("weather_coordinator.error", error=str(e))


_coordinator_task: asyncio.Task | None = None


def start_proactive_coordinators() -> None:
    global _coordinator_task
    if _coordinator_task is None or _coordinator_task.done():
        _coordinator_task = asyncio.create_task(_weather_coordinator())
        log.info("proactive.coordinators_started")


async def stop_proactive_coordinators() -> None:
    global _coordinator_task
    if _coordinator_task is not None:
        _coordinator_task.cancel()
        try:
            await _coordinator_task
        except (asyncio.CancelledError, Exception):
            pass
        _coordinator_task = None
