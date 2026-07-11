"""Map LangGraph astream_events (v2) to the compact UI event feed.

One pass over the event stream powers both the chat transcript and the live
mission-control panel:
  - node enter/exit for known agents  -> agent_enter / agent_exit
  - streamed model tokens (agent-tagged) -> token
  - node output deltas -> plan_updated / handoff / message
  - tool run boundaries -> tool_start / tool_end
  - model-end usage -> per-session telemetry -> telemetry
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from time import perf_counter
from typing import Any

from odyssey.agents.base import BOOKING_CONFIRM, SUPERVISOR, summarize
from odyssey.core.logging import get_logger
from odyssey.core.observability import langfuse_config
from odyssey.core.telemetry import TOOL_CALLS, get_session_telemetry
from odyssey.graph.registry import AGENT_REGISTRY, registry_public
from odyssey.graph.runtime import GraphRuntime
from odyssey.graph.state import turn_input
from odyssey.schemas.events import (
    UIEvent,
    ev_agent_enter,
    ev_agent_exit,
    ev_approval_required,
    ev_booking_updated,
    ev_done,
    ev_error,
    ev_handoff,
    ev_message,
    ev_options,
    ev_plan_updated,
    ev_session_start,
    ev_telemetry,
    ev_token,
    ev_tool_end,
    ev_tool_start,
)

log = get_logger(__name__)


def known_agents() -> set[str]:
    return {SUPERVISOR} | set(AGENT_REGISTRY.keys())


def _agent_from_tags(tags: list[str], fallback: str) -> str:
    for t in tags:
        if t.startswith("agent:"):
            return t.split(":", 1)[1]
    return fallback


def _chunk_text(chunk: Any) -> str:
    if chunk is None:
        return ""
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    # some providers stream content as a list of blocks
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def _extract_usage(output: Any) -> tuple[int, int, str | None]:
    """Pull (input_tokens, output_tokens, model) from an on_chat_model_end output,
    tolerating the several shapes LangChain uses across providers."""
    msg = output
    # LLMResult-like: dig to the message
    gens = getattr(output, "generations", None)
    if gens:
        try:
            msg = gens[0][0].message
        except Exception:
            msg = output
    usage = getattr(msg, "usage_metadata", None)
    model = None
    meta = getattr(msg, "response_metadata", None) or {}
    if isinstance(meta, dict):
        model = meta.get("model_name") or meta.get("model")
    if usage:
        return int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0)), model
    return 0, 0, model


def _agents_public() -> list[dict]:
    supervisor = {
        "name": SUPERVISOR,
        "description": "Orchestrates the team and routes work.",
        "phase": 1,
        "role": "supervisor",
    }
    return [supervisor, *({**a, "role": "specialist"} for a in registry_public())]


async def stream_turn(
    runtime: GraphRuntime, user_id: str, session_id: str, text: str
) -> AsyncIterator[UIEvent]:
    """Run one fresh conversational turn and yield UIEvents."""
    yield ev_session_start(session_id, _agents_public())
    inputs = turn_input(user_id, session_id, text)
    async for ev in _run_stream(runtime, user_id, session_id, inputs):
        yield ev


async def resume_turn(
    runtime: GraphRuntime, user_id: str, session_id: str, decision: dict
) -> AsyncIterator[UIEvent]:
    """Resume a graph paused at the approval gate with the user's decision."""
    from langgraph.types import Command

    async for ev in _run_stream(runtime, user_id, session_id, Command(resume=decision)):
        yield ev


def _extract_update(out: Any) -> dict | None:
    """Node output is a dict, or a Command whose .update holds the state delta."""
    if isinstance(out, dict):
        return out
    upd = getattr(out, "update", None)
    return upd if isinstance(upd, dict) else None


async def _run_stream(
    runtime: GraphRuntime, user_id: str, session_id: str, graph_input: Any
) -> AsyncIterator[UIEvent]:
    config = {
        "configurable": {"thread_id": session_id},
        **langfuse_config(session_id, user_id),
    }
    tel = get_session_telemetry(session_id)
    current_agent = SUPERVISOR
    turn_start = perf_counter()
    # booking_confirm is an internal gate (not a registered agent) but we still emit
    # its messages/booking updates, attributed to the booking agent.
    processable = known_agents() | {BOOKING_CONFIRM}

    try:
        async for event in runtime.graph.astream_events(graph_input, config=config, version="v2"):
            etype = event.get("event")
            name = event.get("name")
            tags = event.get("tags") or []
            data = event.get("data") or {}
            agent = _agent_from_tags(tags, current_agent)

            if etype == "on_chain_start" and name in known_agents():
                current_agent = name
                tel.agent_steps += 1
                yield ev_agent_enter(name)

            elif etype == "on_chain_end" and name in processable:
                update = _extract_update(data.get("output"))
                if update:
                    for hv in update.get("tool_events", []) or []:
                        if hv.get("kind") == "handoff":
                            yield ev_handoff(hv["from"], hv["to"], hv.get("reason", ""))
                    if update.get("itinerary"):
                        yield ev_plan_updated(update["itinerary"])
                    if update.get("options"):
                        yield ev_options(update["options"])
                    if update.get("confirmed_bookings") is not None:
                        yield ev_booking_updated(update["confirmed_bookings"])
                    for m in update.get("messages", []) or []:
                        content = getattr(m, "content", None)
                        if content:
                            who = getattr(m, "name", None) or name
                            yield ev_message(who, content if isinstance(content, str) else str(content))
                if name in known_agents():
                    yield ev_agent_exit(name)

            elif etype == "on_chat_model_stream":
                text_chunk = _chunk_text(data.get("chunk"))
                if text_chunk:
                    yield ev_token(agent, text_chunk)

            elif etype == "on_chat_model_end":
                itok, otok, model = _extract_usage(data.get("output"))
                if itok or otok:
                    tel.add_usage(itok, otok, model)
                    yield ev_telemetry(tel.snapshot())

            elif etype == "on_tool_start":
                tel.tool_calls += 1
                preview = summarize(str(data.get("input", "")), 100)
                yield ev_tool_start(agent, name or "tool", preview)

            elif etype == "on_tool_end":
                summary = _tool_summary(data.get("output"))
                TOOL_CALLS.labels(name or "tool", "ok").inc()
                yield ev_tool_end(agent, name or "tool", summary, 0.0, True)

    except Exception as e:  # graceful degradation - surface, do not crash the stream
        log.exception("stream.error", session_id=session_id)
        yield ev_error(current_agent, f"An agent step failed: {e}", "You can retry or refine your request.")

    # If the graph paused at the human-in-the-loop gate, surface the approval request
    # instead of ending the turn.
    interrupts = []
    snapshot = None
    try:
        snapshot = await runtime.graph.aget_state(config)
        interrupts = list(getattr(snapshot, "interrupts", None) or [])
    except Exception:  # pragma: no cover
        pass

    # Record session metadata for the trips/history list (best-effort).
    try:
        if snapshot is not None and runtime.store is not None:
            from odyssey.memory.store_repo import record_session

            itin = (snapshot.values or {}).get("itinerary") or {}
            await record_session(
                runtime.store, user_id, session_id, destination=itin.get("destination")
            )
    except Exception:  # pragma: no cover
        pass

    tel.last_latency_ms = (perf_counter() - turn_start) * 1000
    yield ev_telemetry(tel.snapshot())
    if interrupts:
        yield ev_approval_required(interrupts[0].value)
    else:
        yield ev_done(session_id)


def _tool_summary(out: Any) -> str:
    """Human summary from a ToolMessage / content_and_artifact output."""
    content = getattr(out, "content", out)
    if isinstance(content, str):
        return summarize(content, 140)
    return summarize(str(content), 140)
