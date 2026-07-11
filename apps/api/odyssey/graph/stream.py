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
from typing import Any

from odyssey.agents.base import SUPERVISOR, summarize
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
    ev_done,
    ev_error,
    ev_handoff,
    ev_message,
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
    supervisor = {"name": SUPERVISOR, "description": "Orchestrates the team and routes work.", "phase": 1}
    return [supervisor, *registry_public()]


async def stream_turn(
    runtime: GraphRuntime, user_id: str, session_id: str, text: str
) -> AsyncIterator[UIEvent]:
    """Run one conversational turn and yield UIEvents."""
    config = {
        "configurable": {"thread_id": session_id},
        **langfuse_config(session_id, user_id),
    }
    inputs = turn_input(user_id, session_id, text)
    tel = get_session_telemetry(session_id)
    current_agent = SUPERVISOR

    yield ev_session_start(session_id, _agents_public())

    try:
        async for event in runtime.graph.astream_events(inputs, config=config, version="v2"):
            etype = event.get("event")
            name = event.get("name")
            tags = event.get("tags") or []
            data = event.get("data") or {}
            agent = _agent_from_tags(tags, current_agent)

            if etype == "on_chain_start" and name in known_agents():
                current_agent = name
                tel.agent_steps += 1
                yield ev_agent_enter(name)

            elif etype == "on_chain_end" and name in known_agents():
                out = data.get("output")
                if isinstance(out, dict):
                    for hv in out.get("tool_events", []) or []:
                        if hv.get("kind") == "handoff":
                            yield ev_handoff(hv["from"], hv["to"], hv.get("reason", ""))
                    if out.get("itinerary"):
                        yield ev_plan_updated(out["itinerary"])
                    for m in out.get("messages", []) or []:
                        content = getattr(m, "content", None)
                        if content:
                            yield ev_message(name, content if isinstance(content, str) else str(content))
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
                out = data.get("output")
                summary = _tool_summary(out)
                TOOL_CALLS.labels(name or "tool", "ok").inc()
                yield ev_tool_end(agent, name or "tool", summary, 0.0, True)

    except Exception as e:  # graceful degradation - surface, do not crash the stream
        log.exception("stream.error", session_id=session_id)
        yield ev_error(current_agent, f"An agent step failed: {e}", "You can retry or refine your request.")

    tel_snapshot = tel.snapshot()
    yield ev_telemetry(tel_snapshot)
    yield ev_done(session_id)


def _tool_summary(out: Any) -> str:
    """Human summary from a ToolMessage / content_and_artifact output."""
    content = getattr(out, "content", out)
    if isinstance(content, str):
        return summarize(content, 140)
    return summarize(str(content), 140)
