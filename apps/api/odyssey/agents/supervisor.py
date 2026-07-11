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

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from odyssey.agents.base import (
    DESTINATION,
    LOGISTICS,
    MEMORY,
    PLANNER,
    SUPERVISOR,
    agent_config,
    handoff_event,
    safe_structured,
    tool_event,
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

MAX_HOPS = 8
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
    if MEMORY in AGENT_REGISTRY and not ctx.get("memory_loaded"):
        return MEMORY
    if not ctx.get("research_done"):
        return DESTINATION
    if not itinerary:
        return PLANNER
    if LOGISTICS in AGENT_REGISTRY and not ctx.get("logistics_done"):
        return LOGISTICS
    return DONE


def _valid_targets() -> set[str]:
    return set(AGENT_REGISTRY.keys()) | {DONE}


_DEFAULT_REASONS = {
    MEMORY: "recalling your saved preferences before planning",
    DESTINATION: "gathering destination facts, weather, and points of interest",
    PLANNER: "building the day-by-day itinerary",
    LOGISTICS: "validating day-of timing and travel between stops",
}


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
        from datetime import date

        date_note = (
            f"Today's date is {date.today().isoformat()}. Interpret months or seasons without a "
            f"year as the next upcoming occurrence; never use a past year."
        )
        extract = await safe_structured(
            llm,
            BriefExtract,
            [SystemMessage(content=SUPERVISOR_BRIEF_EXTRACT + "\n" + date_note), *messages],
            agent=SUPERVISOR,
        )
        if extract is not None:
            brief = _merge_brief(brief, extract)
            updates["trip_brief"] = brief

    brief = brief or {}
    heuristic = _heuristic_next(brief, ctx, itinerary)

    # 2. Routing. The forward pipeline (memory -> research -> plan -> logistics) is
    # deterministic so steps never skip or duplicate; we only consult the LLM router
    # at the completion point, where a fresh user request may re-engage a specialist.
    # This also avoids an LLM call on every hop.
    counts = {} if hops == 0 else dict(ctx.get("_route_counts") or {})

    if heuristic != DONE:
        next_agent = heuristic
        reason = _DEFAULT_REASONS.get(heuristic, "continuing")
    else:
        route_prompt = SUPERVISOR_ROUTE.format(
            agents=registry_descriptions(),
            brief_status=("yes: " + brief["destination"]) if brief.get("destination") else "no destination yet",
            research_status="yes" if ctx.get("research_done") else "no",
            itinerary_status="yes" if itinerary else "no",
            error_status=str(len(state.get("errors", []))) + " logged",
            hops=hops,
        )
        # Include the latest user message so the router can detect a follow-up
        # change request (e.g. "swap the rainy-day outdoor plans for indoor ones").
        last_user = next(
            (m for m in reversed(messages) if isinstance(m, HumanMessage)), None
        )
        route_msgs: list = [SystemMessage(content=route_prompt)]
        if last_user is not None:
            route_msgs.append(HumanMessage(content=f"Latest traveler message: {last_user.content}"))
        decision = await safe_structured(llm, RouteDecision, route_msgs, agent=SUPERVISOR)
        llm_choice = decision.next_agent if decision else None
        llm_reason = decision.reason if decision else None
        if llm_choice in AGENT_REGISTRY and counts.get(llm_choice, 0) < 1:
            next_agent = llm_choice
            reason = llm_reason or f"following up with {llm_choice}"
        else:
            next_agent = DONE
            reason = llm_reason or "the plan is complete"

    # Hard safety rails (always kept).
    if next_agent != DONE and not brief.get("destination"):
        next_agent, reason = DONE, "need a destination from the traveler first"
    if hops >= MAX_HOPS:
        next_agent, reason = DONE, "reached the work limit for this turn"
    if next_agent != DONE and counts.get(next_agent, 0) >= 2:
        next_agent, reason = DONE, "already consulted that specialist; wrapping up"

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

    # Write salient, durable traveler facts to long-term memory at end-of-turn.
    if itinerary:
        try:
            from langgraph.config import get_store

            from odyssey.memory.store_repo import extract_and_store

            store = get_store()
            if store is not None:
                stored = await extract_and_store(
                    store, state.get("user_id", ""), messages, brief
                )
                if stored:
                    updates.setdefault("tool_events", []).append(
                        tool_event(SUPERVISOR, "save_memory", f"{len(stored)} facts remembered", True, 0)
                    )
        except Exception as e:  # never let memory writes break the turn
            log.warning("memory.write_failed", error=str(e))

    log.info("supervisor.done", has_itinerary=bool(itinerary))
    return updates


def route_from_supervisor(state: dict) -> str:
    """Conditional-edge function: read the supervisor's decision."""
    nxt = state.get("next_agent")
    if nxt and nxt in AGENT_REGISTRY:
        return nxt
    return DONE
