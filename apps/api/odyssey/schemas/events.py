"""Compact UI event schema.

LangGraph astream_events (v2) are mapped to these events and streamed over SSE.
The same feed powers the chat transcript and the live mission-control panel, so
the schema is intentionally small and stable.
"""

from __future__ import annotations

import time
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class UIEventType(StrEnum):
    session_start = "session_start"
    agent_enter = "agent_enter"
    agent_exit = "agent_exit"
    token = "token"
    message = "message"
    tool_start = "tool_start"
    tool_end = "tool_end"
    handoff = "handoff"
    plan_updated = "plan_updated"
    options = "options"
    approval_required = "approval_required"
    booking_updated = "booking_updated"
    telemetry = "telemetry"
    error = "error"
    done = "done"


class UIEvent(BaseModel):
    type: UIEventType
    ts: float = Field(default_factory=lambda: time.time())
    agent: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    def sse(self) -> dict[str, str]:
        """Shape expected by sse_starlette.EventSourceResponse."""
        import orjson

        return {"event": str(self.type), "data": orjson.dumps(self.model_dump()).decode()}


# ---- Convenience constructors (keep call sites terse and consistent) ----


def ev_session_start(session_id: str, agents: list[dict]) -> UIEvent:
    return UIEvent(
        type=UIEventType.session_start,
        data={"session_id": session_id, "agents": agents},
    )


def ev_agent_enter(agent: str, reason: str | None = None) -> UIEvent:
    return UIEvent(type=UIEventType.agent_enter, agent=agent, data={"reason": reason})


def ev_agent_exit(agent: str) -> UIEvent:
    return UIEvent(type=UIEventType.agent_exit, agent=agent)


def ev_token(agent: str, text: str) -> UIEvent:
    return UIEvent(type=UIEventType.token, agent=agent, data={"text": text})


def ev_message(agent: str, text: str, role: Literal["assistant"] = "assistant") -> UIEvent:
    return UIEvent(type=UIEventType.message, agent=agent, data={"text": text, "role": role})


def ev_tool_start(agent: str, tool: str, args_preview: str) -> UIEvent:
    return UIEvent(
        type=UIEventType.tool_start,
        agent=agent,
        data={"tool": tool, "args_preview": args_preview},
    )


def ev_tool_end(agent: str, tool: str, summary: str, duration_ms: float, ok: bool) -> UIEvent:
    return UIEvent(
        type=UIEventType.tool_end,
        agent=agent,
        data={"tool": tool, "summary": summary, "duration_ms": round(duration_ms, 1), "ok": ok},
    )


def ev_handoff(from_agent: str, to_agent: str, reason: str) -> UIEvent:
    return UIEvent(
        type=UIEventType.handoff,
        agent=from_agent,
        data={"from": from_agent, "to": to_agent, "reason": reason},
    )


def ev_plan_updated(itinerary: dict) -> UIEvent:
    return UIEvent(type=UIEventType.plan_updated, data={"itinerary": itinerary})


def ev_options(options: dict) -> UIEvent:
    return UIEvent(type=UIEventType.options, data={"options": options})


def ev_approval_required(payload: dict) -> UIEvent:
    return UIEvent(type=UIEventType.approval_required, data=payload)


def ev_booking_updated(confirmed: list[dict]) -> UIEvent:
    return UIEvent(type=UIEventType.booking_updated, data={"confirmed_bookings": confirmed})


def ev_telemetry(snapshot: dict) -> UIEvent:
    return UIEvent(type=UIEventType.telemetry, data=snapshot)


def ev_error(agent: str | None, message: str, fallback: str | None = None) -> UIEvent:
    return UIEvent(type=UIEventType.error, agent=agent, data={"message": message, "fallback": fallback})


def ev_done(session_id: str) -> UIEvent:
    return UIEvent(type=UIEventType.done, data={"session_id": session_id})
