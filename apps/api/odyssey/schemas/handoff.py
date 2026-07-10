"""Typed handoff protocol between agents.

Handoffs are explicit. An agent node returns a Command(goto=..., update=...) and
records a Handoff so the mission-control UI can render the arrow with its reason.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Handoff(BaseModel):
    from_agent: str
    to_agent: str
    reason: str  # why control is moving (shown in the trace panel)
    payload: dict = Field(default_factory=dict)  # typed per target agent
    context_keys: list[str] = Field(default_factory=list)  # keys the receiver should read
    require_response: bool = True  # does control return to the sender afterward
