"""Supervisor / Orchestrator.

Custom (not prebuilt) so we control routing and the trace stream. Each turn it:
  1. Extracts and merges a structured trip brief from the conversation.
  2. Decides the next agent with the LLM, constrained by hard guardrails (a
     destination must exist before specialists run; hop and per-agent visit caps
     guarantee progress and termination).
  3. On "done", streams a warm wrap-up (or a clarifying question).

Routing is registry-driven: the agent menu in the prompt is built from
AGENT_REGISTRY, so new agents are considered automatically.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from odyssey.agents.base import (
    DESTINATION,
    PLANNER,
    SUPERVISOR,
    agent_config,
    handoff_event,
    safe_structured,
)
from odyssey.core.logging import get_logger
from odyssey.graph.registry import AGENT_REGISTRY, registry_descriptions
from odyssey.prompts.agents import (
    SUPERVISOR_BRIEF_EXTRACT,
    SUPERVISOR_FINALIZE,
    SUPERVISOR_ROUTE,
)
from odyssey.providers.llm_provider import get_chat_model

log = get_logger(__name__)

MAX_HOPS = 6
DONE = "done"


class BriefExtract(BaseModel):
    destination: str | None = None
    origin: str | None = None
    start_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    end_date: str | None = None
    duration_days: int | None = None
    adults: int | None = None
    children: int | None = None
    budget_total: float | None = None
    currency: str | None = None
    pace: str | None = Field(default=None, description="relaxed|balanced|packed")
    interests: list[str] | None = None
    must_haves: list[str] | None = None
    must_avoids: list[str] | None = None
    style: str | None = None


class RouteDecision(BaseModel):
    next_agent: str = Field(description="an agent name or 'done'")
    reason: str = Field(description="one line, shown in the mission-control panel")


def _merge_brief(existing: dict | None, ex: BriefExtract) -> dict:
    brief = dict(existing or {})
    d = ex.model_dump(exclude_none=True)
    # Nested-ish fields
    if "adults" in d or "children" in d:
        party = dict(brief.get("party") or {})
        if "adults" in d:
            party["adults"] = d.pop("adults")
        if "children" in d:
            party["children"] = d.pop("children")
        brief["party"] = party
    if "budget_total" in d or "currency" in d:
        budget = dict(brief.get("budget") or {})
        if "budget_total" in d:
            budget["total"] = d.pop("budget_total")
        if "currency" in d:
            budget["currency"] = d.pop("currency")
        brief["budget"] = budget
    for k, v in d.items():
        if isinstance(v, list) and not v:
            continue
        brief[k] = v
    return brief


def _heuristic_next(brief: dict, ctx: dict, itinerary: dict | None) -> str:
    if not brief.get("destination"):
        return DONE
    if not ctx.get("research_done"):
        return DESTINATION
    if not itinerary:
        return PLANNER
    return DONE


def _valid_targets() -> set[str]:
    return set(AGENT_REGISTRY.keys()) | {DONE}


async def supervisor_node(state: dict) -> dict:
    llm = get_chat_model()
    messages = state.get("messages", [])
    brief = state.get("trip_brief")
    ctx = state.get("context") or {}
    itinerary = state.get("itinerary")
    hops = int(state.get("hops", 0))

    # 1. Extract / merge the brief (only meaningful early; cheap and idempotent).
    updates: dict = {"active_agent": SUPERVISOR}
    if not itinerary:  # once a plan exists we stop re-extracting
        extract = await safe_structured(
            llm,
            BriefExtract,
            [SystemMessage(content=SUPERVISOR_BRIEF_EXTRACT), *messages],
            agent=SUPERVISOR,
        )
        if extract is not None:
            brief = _merge_brief(brief, extract)
            updates["trip_brief"] = brief

    brief = brief or {}
    heuristic = _heuristic_next(brief, ctx, itinerary)

    # 2. LLM routing decision, constrained by guardrails.
    route_prompt = SUPERVISOR_ROUTE.format(
        agents=registry_descriptions(),
        brief_status="yes: " + brief["destination"] if brief.get("destination") else "no destination yet",
        research_status="yes" if ctx.get("research_done") else "no",
        itinerary_status="yes" if itinerary else "no",
        error_status=str(len(state.get("errors", []))) + " logged",
        hops=hops,
    )
    decision = await safe_structured(
        llm, RouteDecision, [SystemMessage(content=route_prompt)], agent=SUPERVISOR
    )

    next_agent = decision.next_agent if decision else heuristic
    reason = decision.reason if decision else "routing by rule"

    # Hard guardrails (production supervisors always keep these rails).
    counts = dict(ctx.get("_route_counts") or {})
    if next_agent not in _valid_targets():
        next_agent, reason = heuristic, f"'{next_agent}' is not a known agent; routing by rule"
    if next_agent != DONE and not brief.get("destination"):
        next_agent, reason = DONE, "need a destination from the traveler first"
    if hops >= MAX_HOPS:
        next_agent, reason = DONE, "reached the work limit for this turn"
    if next_agent != DONE and counts.get(next_agent, 0) >= 2:
        next_agent = heuristic if heuristic != next_agent else DONE
        reason = f"already consulted {reason.split()[0] if reason else next_agent}; moving on"

    # 3a. Route to a specialist.
    if next_agent != DONE:
        counts[next_agent] = counts.get(next_agent, 0) + 1
        updates["context"] = {"_route_counts": counts}
        updates["hops"] = hops + 1
        updates["next_agent"] = next_agent
        updates["tool_events"] = [handoff_event(SUPERVISOR, next_agent, reason)]
        log.info("supervisor.route", to=next_agent, reason=reason, hops=hops + 1)
        return updates

    # 3b. Done: stream a wrap-up or a clarifying question.
    final = await llm.ainvoke(
        [SystemMessage(content=SUPERVISOR_FINALIZE), *messages],
        config=agent_config(SUPERVISOR),
    )
    content = final.content if isinstance(final.content, str) else str(final.content)
    updates["next_agent"] = DONE
    updates["messages"] = [AIMessage(content=content, name=SUPERVISOR)]
    log.info("supervisor.done", has_itinerary=bool(itinerary))
    return updates


def route_from_supervisor(state: dict) -> str:
    """Conditional-edge function: read the supervisor's decision."""
    nxt = state.get("next_agent")
    if nxt and nxt in AGENT_REGISTRY:
        return nxt
    return DONE
