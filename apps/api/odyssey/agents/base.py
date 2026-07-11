"""Shared agent helpers: node names, event builders, artifact extraction, and a
resilient structured-output call used across specialists.
"""

from __future__ import annotations

import time
from typing import Any, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, ToolMessage
from pydantic import BaseModel

from odyssey.core.logging import get_logger

log = get_logger(__name__)

# Canonical node names (also the registry keys and UI node ids).
SUPERVISOR = "supervisor"
DESTINATION = "destination_intelligence"
PLANNER = "trip_planner"
LOGISTICS = "logistics"
MEMORY = "memory"
BOOKING = "booking"
SUPPORT = "support"

T = TypeVar("T", bound=BaseModel)


def agent_config(agent: str, extra_tags: list[str] | None = None) -> dict:
    """Config that tags every child runnable with the agent, so the stream mapper
    can attribute tokens and tool calls to the right node."""
    tags = [f"agent:{agent}"]
    if extra_tags:
        tags.extend(extra_tags)
    return {"tags": tags}


def tool_event(agent: str, tool: str, summary: str, ok: bool, duration_ms: float) -> dict:
    return {
        "kind": "tool",
        "agent": agent,
        "tool": tool,
        "summary": summary,
        "ok": ok,
        "duration_ms": round(duration_ms, 1),
        "ts": time.time(),
    }


def handoff_event(from_agent: str, to_agent: str, reason: str) -> dict:
    return {
        "kind": "handoff",
        "from": from_agent,
        "to": to_agent,
        "reason": reason,
        "ts": time.time(),
    }


def error_event(agent: str, message: str, fallback: str | None = None) -> dict:
    return {"agent": agent, "message": message, "fallback": fallback, "ts": time.time()}


def extract_tool_artifacts(messages: list[BaseMessage]) -> dict[str, list[dict]]:
    """Collect structured artifacts produced by tools during a specialist run,
    grouped by tool name. Tools use response_format=content_and_artifact, so the
    typed payload is on ToolMessage.artifact."""
    out: dict[str, list[dict]] = {}
    for m in messages:
        if isinstance(m, ToolMessage) and getattr(m, "artifact", None):
            art = m.artifact
            if isinstance(art, dict):
                out.setdefault(m.name or "unknown", []).append(art)
    return out


async def safe_structured(
    llm: BaseChatModel,
    schema: type[T],
    messages: list[BaseMessage],
    *,
    agent: str,
    config: dict | None = None,
) -> T | None:
    """Call with_structured_output with a guard. Returns None on failure so callers
    can degrade gracefully rather than crash the graph."""
    try:
        structured = llm.with_structured_output(schema)
        cfg = agent_config(agent)
        if config:
            cfg = {**cfg, **config}
        result = await structured.ainvoke(messages, config=cfg)
        return result  # type: ignore[return-value]
    except Exception as e:  # pragma: no cover - depends on live model
        log.warning("structured_output.failed", agent=agent, schema=schema.__name__, error=str(e))
        return None


def summarize(text: str, n: int = 140) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def as_dict(model: BaseModel | dict | None) -> dict | None:
    if model is None:
        return None
    if isinstance(model, dict):
        return model
    return model.model_dump(mode="json")
