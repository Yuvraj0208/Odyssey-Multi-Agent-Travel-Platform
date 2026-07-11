"""Logistics Coordinator agent.

Validates that each day is physically doable: computes real walking travel times
between the day's stops (OSRM, with a fallback), annotates each item with the hop
to the next stop, tags days as feasible or over-packed, and writes a short
feasibility briefing. Advises rather than silently rewriting the plan; a badly
over-packed day is flagged clearly so the traveler (or a follow-up planning turn)
can adjust.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from odyssey.agents.base import LOGISTICS, agent_config, error_event, tool_event
from odyssey.core.logging import get_logger
from odyssey.graph.registry import AgentSpec, register
from odyssey.providers.tools.routing import plan_day_route

log = get_logger(__name__)

# A day is flagged if walking between stops alone exceeds this.
_PACKED_TRAVEL_MIN = 150.0
_LONG_LEG_MIN = 40.0


async def _route_day(coords: list[list[float]]) -> dict:
    msg = await plan_day_route.ainvoke(
        {"type": "tool_call", "id": "route", "name": "plan_day_route", "args": {"coords": coords, "mode": "walking"}},
        config=agent_config(LOGISTICS),
    )
    return getattr(msg, "artifact", {}) or {}


async def logistics_node(state: dict) -> dict:
    itinerary = state.get("itinerary")
    if not itinerary or not itinerary.get("days"):
        return {
            "context": {"logistics_done": True},
            "errors": [error_event(LOGISTICS, "no itinerary to validate", "returned to supervisor")],
            "active_agent": LOGISTICS,
        }

    days = itinerary["days"]
    events = []
    day_reports = []
    try:
        for day in days:
            geo_items = [it for it in day.get("items", []) if it.get("geo")]
            coords = [[it["geo"]["lng"], it["geo"]["lat"]] for it in geo_items]
            if len(coords) < 2:
                day["travel_min"] = 0.0
                day["feasible"] = True
                continue
            art = await _route_day(coords)
            legs = art.get("legs", [])
            # annotate each stop with the hop to the next
            for i, it in enumerate(geo_items[:-1]):
                if i < len(legs):
                    it["transit_to_next_min"] = legs[i]["duration_min"]
                    it["transit_to_next_km"] = legs[i]["distance_km"]
                    it["transit_mode"] = "walking"
            total = art.get("total_min", 0.0)
            day["travel_min"] = total
            longest = max((leg["duration_min"] for leg in legs), default=0.0)
            day["feasible"] = total <= _PACKED_TRAVEL_MIN and longest <= _LONG_LEG_MIN
            events.append(
                tool_event(LOGISTICS, "plan_day_route", f"Day {day['day']}: {total:.0f} min walking", True, 0)
            )
            day_reports.append(
                {"day": day["day"], "travel_min": total, "feasible": day["feasible"], "longest_leg": longest}
            )
    except Exception as e:  # graceful degradation
        log.warning("logistics.failed", error=str(e))
        return {
            "context": {"logistics_done": True},
            "errors": [error_event(LOGISTICS, f"routing failed: {e}", "kept plan without timing checks")],
            "active_agent": LOGISTICS,
        }

    packed = [r for r in day_reports if not r["feasible"]]
    if packed:
        worst = ", ".join(f"Day {r['day']} ({r['travel_min']:.0f} min on foot)" for r in packed)
        note = (
            f"I checked travel times between every stop. Most days flow well, but {worst} "
            f"involve a lot of walking - consider a taxi or metro for the longer hops, or trimming a stop."
        )
    else:
        avg = sum(r["travel_min"] for r in day_reports) / max(1, len(day_reports))
        note = (
            f"Timing checks out: every day is comfortably walkable "
            f"(~{avg:.0f} min on foot between stops on average). You're good to go."
        )

    return {
        "itinerary": itinerary,  # re-emit with transit annotations + feasibility
        "context": {"logistics_done": True, "logistics_report": day_reports},
        "tool_events": events,
        "messages": [AIMessage(content=note, name=LOGISTICS)],
        "active_agent": LOGISTICS,
    }


register(
    AgentSpec(
        name=LOGISTICS,
        description=(
            "Validates day-of timing: computes real travel times between stops, annotates transit, "
            "and flags over-packed days. Consult after an itinerary is drafted to sanity-check feasibility."
        ),
        build=lambda: logistics_node,
        phase=2,
    )
)
