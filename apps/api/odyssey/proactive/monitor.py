"""Conditions monitor for proactive re-planning.

Re-fetches live weather for a saved itinerary and, when a day with outdoor items
is now forecast to be adverse, publishes a weather_changed event on the bus. The
weather coordinator turns that into a user notification with a one-click re-plan
prompt. This is the event-driven trigger described in the spec (destination-side
signal -> planner-side reaction), not a request-response poll baked into the turn.
"""

from __future__ import annotations

from odyssey.core.events import CH_WEATHER_CHANGED, get_event_bus
from odyssey.core.logging import get_logger
from odyssey.providers.tools.weather import get_weather

log = get_logger(__name__)

_ADVERSE = ("rain", "drizzle", "snow", "thunder", "showers")
_OUTDOOR_TYPES = {"attraction", "activity"}


def _is_outdoor(item: dict) -> bool:
    if item.get("weather_note"):
        return False  # already flagged/handled by the planner
    return item.get("type") in _OUTDOOR_TYPES


def _adverse(day_weather: dict) -> bool:
    cond = (day_weather.get("condition") or "").lower()
    if any(k in cond for k in _ADVERSE):
        return True
    return (day_weather.get("precip_prob_pct") or 0) >= 50


async def check_conditions(state: dict, *, publish: bool = True, force_demo: bool = False) -> list[dict]:
    """Return a list of detected issues; optionally publish weather_changed events.

    force_demo synthesizes one issue from the first outdoor day when live weather is
    benign, so the full event-driven path (bus -> coordinator -> notification -> UI)
    can be demonstrated on demand. It flows through the same real machinery.
    """
    itinerary = state.get("itinerary")
    if not itinerary or not itinerary.get("days"):
        return []
    center = itinerary.get("center") or {}
    if not center.get("lat"):
        return []

    user_id = state.get("user_id")
    session_id = state.get("session_id")

    # Live re-fetch (default forecast window).
    content, art = await _fetch_weather(center["lat"], center["lng"])
    forecast = art.get("days", []) if isinstance(art, dict) else []

    issues: list[dict] = []
    bus = get_event_bus()
    for i, day in enumerate(itinerary["days"]):
        outdoor = [it["title"] for it in day.get("items", []) if _is_outdoor(it)]
        if not outdoor:
            continue
        dw = forecast[i] if i < len(forecast) else None
        if not dw or not _adverse(dw):
            continue
        issues.append(
            {
                "session_id": session_id,
                "user_id": user_id,
                "day": day.get("day", i + 1),
                "date": dw.get("date"),
                "condition": dw.get("condition"),
                "precip_prob_pct": dw.get("precip_prob_pct"),
                "outdoor_items": outdoor,
            }
        )

    if not issues and force_demo:
        for day in itinerary["days"]:
            outdoor = [it["title"] for it in day.get("items", []) if _is_outdoor(it)]
            if outdoor:
                issues.append(
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "day": day.get("day"),
                        "date": forecast[0].get("date") if forecast else None,
                        "condition": "rain",
                        "precip_prob_pct": 80,
                        "outdoor_items": outdoor,
                    }
                )
                break

    if publish and user_id:
        for issue in issues:
            await bus.publish(CH_WEATHER_CHANGED, issue)
    if issues:
        log.info("monitor.issues", session_id=session_id, count=len(issues), demo=force_demo)
    return issues


async def _fetch_weather(lat: float, lng: float):
    # Invoke the tool as a tool-call so we get the structured artifact back.
    msg = await get_weather.ainvoke(
        {"type": "tool_call", "id": "monitor", "name": "get_weather", "args": {"lat": lat, "lng": lng}}
    )
    return msg.content, getattr(msg, "artifact", {}) or {}
