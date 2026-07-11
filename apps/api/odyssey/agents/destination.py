"""Destination Intelligence agent.

A real tool-calling ReAct subgraph (create_react_agent) bound to the open tourism
tools. The wrapper node runs the loop, then extracts typed artifacts from the tool
messages into the shared context so the planner has grounded, real-world data.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from odyssey.agents.base import (
    DESTINATION,
    agent_config,
    error_event,
    extract_tool_artifacts,
    summarize,
    tool_event,
)
from odyssey.core.logging import get_logger
from odyssey.graph.registry import AgentSpec, register
from odyssey.prompts.agents import DESTINATION_INTEL
from odyssey.providers.llm_provider import get_chat_model
from odyssey.providers.tools import DESTINATION_TOOLS

log = get_logger(__name__)


@lru_cache
def _agent():
    return create_react_agent(get_chat_model(), DESTINATION_TOOLS, prompt=DESTINATION_INTEL)


def _task_text(brief: dict) -> str:
    dest = brief.get("destination") or "the destination"
    dates = ""
    if brief.get("start_date") and brief.get("end_date"):
        dates = f" for {brief['start_date']} to {brief['end_date']}"
    elif brief.get("duration_days"):
        dates = f" for a {brief['duration_days']}-day trip"
    interests = ", ".join(brief.get("interests") or []) or "general sightseeing"
    return (
        f"Research {dest}{dates}. The traveler is interested in: {interests}. "
        f"Geocode the destination, get the weather, and find matching points of interest, "
        f"then give a short briefing."
    )


async def destination_node(state: dict) -> dict:
    brief = state.get("trip_brief") or {}
    if not brief.get("destination"):
        return {
            "errors": [error_event(DESTINATION, "no destination in brief", "returned to supervisor")],
            "active_agent": DESTINATION,
        }

    try:
        result = await _agent().ainvoke(
            {"messages": [HumanMessage(content=_task_text(brief))]},
            config={**agent_config(DESTINATION), "recursion_limit": 12},
        )
    except Exception as e:  # graceful degradation - one failing agent never crashes the graph
        log.warning("destination.failed", error=str(e))
        return {
            "errors": [error_event(DESTINATION, f"research failed: {e}", "planner will use partial data")],
            "context": {"research_done": True, "research_error": str(e)},
            "active_agent": DESTINATION,
        }

    msgs = result["messages"]
    arts = extract_tool_artifacts(msgs)

    geo = next((a for a in arts.get("geocode_place", []) if not a.get("error")), None)
    weather = next((a for a in arts.get("get_weather", []) if not a.get("error")), None)
    pois: list[dict] = []
    for a in arts.get("search_pois", []):
        pois.extend(a.get("pois", []))

    overview = ""
    for m in reversed(msgs):
        if isinstance(m, AIMessage) and m.content:
            overview = m.content if isinstance(m.content, str) else str(m.content)
            break

    ctx_destination = None
    if geo:
        ctx_destination = {
            "name": geo.get("name"),
            "lat": geo.get("lat"),
            "lng": geo.get("lng"),
            "country": geo.get("country"),
            "country_code": geo.get("country_code"),
        }

    # Persisted tool feed (native stream events already show these live; this keeps
    # the durable record for resume + the trace panel).
    events = []
    if geo:
        events.append(tool_event(DESTINATION, "geocode_place", summarize(geo.get("name", "")), True, 0))
    if weather:
        events.append(
            tool_event(DESTINATION, "get_weather", f"{len(weather.get('days', []))} day forecast", True, 0)
        )
    events.append(tool_event(DESTINATION, "search_pois", f"{len(pois)} places found", bool(pois), 0))

    context_update = {
        "research_done": True,
        "destination": ctx_destination,
        "weather": weather,
        "pois": pois,
        "overview": overview,
    }

    updates: dict = {
        "context": context_update,
        "tool_events": events,
        "active_agent": DESTINATION,
    }
    if overview:
        updates["messages"] = [AIMessage(content=overview, name=DESTINATION)]
    if geo:
        merged_brief = dict(brief)
        merged_brief["geo"] = {"lat": geo["lat"], "lng": geo["lng"], "name": geo.get("name")}
        updates["trip_brief"] = merged_brief

    return updates


register(
    AgentSpec(
        name=DESTINATION,
        description=(
            "Gathers real-time destination facts: geocoding, weather forecast, and matching "
            "points of interest from open map data. Call before planning."
        ),
        build=lambda: destination_node,
        phase=1,
    )
)
