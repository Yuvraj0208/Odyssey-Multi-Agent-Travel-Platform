"""Personalization / Memory agent.

At the start of a planning turn it recalls the traveler's durable preferences from
long-term memory and injects them into the shared context so every downstream agent
personalizes. Writing salient facts back happens at end-of-turn (see the supervisor's
finalize path, which calls memory.extract_and_store).
"""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.config import get_store

from odyssey.agents.base import MEMORY, error_event, tool_event
from odyssey.core.logging import get_logger
from odyssey.graph.registry import AgentSpec, register
from odyssey.memory.store_repo import recall

log = get_logger(__name__)


def _terms(brief: dict) -> list[str]:
    terms: list[str] = []
    terms += brief.get("interests") or []
    terms += brief.get("must_haves") or []
    if brief.get("destination"):
        terms.append(brief["destination"])
    if brief.get("style"):
        terms.append(brief["style"])
    if brief.get("pace"):
        terms.append(brief["pace"])
    return terms


async def memory_node(state: dict) -> dict:
    brief = state.get("trip_brief") or {}
    user_id = state.get("user_id", "")
    try:
        store = get_store()
    except Exception:
        store = None
    if store is None:
        return {"context": {"memory_loaded": True}, "active_agent": MEMORY}

    try:
        mems = await recall(store, user_id, _terms(brief), limit=6)
    except Exception as e:
        return {
            "context": {"memory_loaded": True},
            "errors": [error_event(MEMORY, f"recall failed: {e}", "planning without memory")],
            "active_agent": MEMORY,
        }

    prefs = [m["text"] for m in mems]
    updates: dict = {
        "context": {"memory_loaded": True, "preferences": prefs},
        "tool_events": [tool_event(MEMORY, "recall_memory", f"{len(prefs)} preferences recalled", True, 0)],
        "active_agent": MEMORY,
    }
    if prefs:
        top = "; ".join(prefs[:3])
        updates["messages"] = [
            AIMessage(
                content=f"Welcome back. I remembered a few things about how you like to travel: {top}. "
                f"I'll factor those in.",
                name=MEMORY,
            )
        ]
    return updates


register(
    AgentSpec(
        name=MEMORY,
        description=(
            "Recalls the traveler's long-term preferences, dislikes, and past trips at the start of "
            "planning and personalizes the plan. Consult first when a returning traveler starts a trip."
        ),
        build=lambda: memory_node,
        phase=2,
    )
)
