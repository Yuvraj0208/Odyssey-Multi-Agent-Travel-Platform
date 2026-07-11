"""Trip Planning agent.

Consumes the trip brief and the destination research (weather + real POIs) and
produces a structured day-by-day itinerary. The LLM reasons over a flat plan schema
(reliable with open models); geo coordinates are attached deterministically from the
real POI list, so venues are never hallucinated and map markers are always accurate.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from odyssey.agents.base import PLANNER, error_event, safe_structured
from odyssey.core.logging import get_logger
from odyssey.graph.registry import AgentSpec, register
from odyssey.prompts.agents import TRIP_PLANNER
from odyssey.providers.llm_provider import get_chat_model
from odyssey.schemas.trip import (
    Geo,
    ItemType,
    Itinerary,
    ItineraryDay,
    ItineraryItem,
)

log = get_logger(__name__)

_PACE_ITEMS = {"relaxed": 3, "balanced": 4, "packed": 6}


class PlanItem(BaseModel):
    day: int = Field(description="1-based day number")
    title: str
    type: str = Field(default="attraction", description="attraction|food|activity|transport|lodging|free")
    poi_name: str | None = Field(default=None, description="exact name from the provided POI list, if any")
    start: str | None = Field(default=None, description="HH:MM")
    end: str | None = None
    description: str | None = None
    cost_estimate: float | None = None
    weather_note: str | None = None


class PlanOutput(BaseModel):
    summary: str
    items: list[PlanItem]


def _num_days(brief: dict) -> int:
    if brief.get("duration_days"):
        return max(1, int(brief["duration_days"]))
    if brief.get("start_date") and brief.get("end_date"):
        try:
            from datetime import date

            d = (date.fromisoformat(brief["end_date"]) - date.fromisoformat(brief["start_date"])).days + 1
            return max(1, d)
        except ValueError:
            pass
    return 3


def _planner_context(brief: dict, ctx: dict) -> str:
    from datetime import date

    pois = ctx.get("pois") or []
    weather = ctx.get("weather") or {}
    lines = [f"Today: {date.today().isoformat()}", f"Destination: {brief.get('destination')}"]
    lines.append(f"Days: {_num_days(brief)} | Pace: {brief.get('pace', 'balanced')}")
    if brief.get("interests"):
        lines.append(f"Interests: {', '.join(brief['interests'])}")
    if ctx.get("preferences"):
        lines.append("Known traveler preferences (personalize to these): " + "; ".join(ctx["preferences"]))
    if brief.get("budget", {}).get("total"):
        lines.append(f"Budget total: {brief['budget']['total']} {brief['budget'].get('currency', 'USD')}")
    if weather.get("days"):
        wl = "; ".join(
            f"{d['date']}: {d['condition']} {d['temp_min_c']}-{d['temp_max_c']}C (rain {d.get('precip_prob_pct')}%)"
            for d in weather["days"][:8]
        )
        lines.append(f"Weather: {wl}")
    if weather.get("rainy_days"):
        lines.append(f"Rainy days (prefer indoor): {', '.join(weather['rainy_days'])}")
    lines.append("\nAvailable points of interest (use exact names as poi_name):")
    for p in pois[:40]:
        cui = f" [{p['cuisine']}]" if p.get("cuisine") else ""
        lines.append(f"- {p['name']} ({p.get('category', 'attraction')}){cui}")
    return "\n".join(lines)


def _poi_index(ctx: dict) -> dict[str, dict]:
    return {p["name"].lower(): p for p in (ctx.get("pois") or []) if p.get("name")}


def _to_itinerary(brief: dict, ctx: dict, plan: PlanOutput) -> Itinerary:
    idx = _poi_index(ctx)
    dest = ctx.get("destination") or {}
    center = Geo(lat=dest["lat"], lng=dest["lng"], name=dest.get("name")) if dest.get("lat") else None
    currency = (brief.get("budget") or {}).get("currency", "USD")

    n = _num_days(brief)
    days: dict[int, ItineraryDay] = {i: ItineraryDay(day=i) for i in range(1, n + 1)}
    for pi in plan.items:
        d = pi.day if pi.day in days else 1
        geo = None
        if pi.poi_name and pi.poi_name.lower() in idx:
            p = idx[pi.poi_name.lower()]
            geo = Geo(lat=p["lat"], lng=p["lng"], name=p["name"])
        try:
            itype = ItemType(pi.type)
        except ValueError:
            itype = ItemType.attraction
        days[d].items.append(
            ItineraryItem(
                type=itype,
                title=pi.title,
                description=pi.description,
                geo=geo,
                start=pi.start,
                end=pi.end,
                cost_estimate=pi.cost_estimate,
                currency=currency,
                source="trip_planner",
                weather_note=pi.weather_note,
            )
        )
    return Itinerary(
        destination=brief.get("destination"),
        center=center,
        days=[days[i] for i in range(1, n + 1)],
        currency=currency,
        summary=plan.summary,
    )


def _fallback_itinerary(brief: dict, ctx: dict) -> Itinerary:
    """Deterministic plan if structured output fails: spread real POIs across days."""
    pois = list(ctx.get("pois") or [])
    n = _num_days(brief)
    per = _PACE_ITEMS.get(brief.get("pace", "balanced"), 4)
    dest = ctx.get("destination") or {}
    center = Geo(lat=dest["lat"], lng=dest["lng"], name=dest.get("name")) if dest.get("lat") else None
    days = []
    k = 0
    for d in range(1, n + 1):
        items = []
        for slot in range(per):
            if k >= len(pois):
                break
            p = pois[k]
            k += 1
            items.append(
                ItineraryItem(
                    type=ItemType.food if p.get("category") == "food" else ItemType.attraction,
                    title=p["name"],
                    geo=Geo(lat=p["lat"], lng=p["lng"], name=p["name"]),
                    start=f"{9 + slot * 2:02d}:00",
                    source="trip_planner(fallback)",
                )
            )
        days.append(ItineraryDay(day=d, items=items))
    return Itinerary(
        destination=brief.get("destination"),
        center=center,
        days=days,
        summary=f"A {n}-day plan for {brief.get('destination')} built from real nearby highlights.",
    )


async def planner_node(state: dict) -> dict:
    brief = state.get("trip_brief") or {}
    ctx = state.get("context") or {}

    if not (ctx.get("pois") or ctx.get("destination")):
        return {
            "errors": [error_event(PLANNER, "no research context", "asked supervisor to gather research")],
            "active_agent": PLANNER,
        }

    messages = [
        SystemMessage(content=TRIP_PLANNER),
        HumanMessage(content=_planner_context(brief, ctx)),
    ]
    plan = await safe_structured(get_chat_model(), PlanOutput, messages, agent=PLANNER)

    if plan and plan.items:
        itinerary = _to_itinerary(brief, ctx, plan)
        note = plan.summary
    else:
        itinerary = _fallback_itinerary(brief, ctx)
        note = itinerary.summary or "Itinerary drafted from nearby highlights."
        log.info("planner.fallback_used")

    return {
        "itinerary": itinerary.model_dump(mode="json"),
        "messages": [AIMessage(content=note or "Here is a draft itinerary.", name=PLANNER)],
        # A fresh plan needs re-validation by logistics.
        "context": {"logistics_done": False},
        "active_agent": PLANNER,
    }


register(
    AgentSpec(
        name=PLANNER,
        description=(
            "Builds and revises the day-by-day itinerary from the brief and destination "
            "research, respecting budget, pace, weather, and real points of interest."
        ),
        build=lambda: planner_node,
        phase=1,
    )
)
