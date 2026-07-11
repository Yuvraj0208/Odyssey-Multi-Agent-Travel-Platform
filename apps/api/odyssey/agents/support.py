"""Traveler Support agent.

Answers questions grounded in the trip state (itinerary, weather, bookings) and
handles cancellations by routing them through the SAME human-in-the-loop approval
gate as bookings - irreversible actions always require explicit confirmation.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import Command
from pydantic import BaseModel, Field

from odyssey.agents.base import (
    BOOKING_CONFIRM,
    SUPERVISOR,
    SUPPORT,
    agent_config,
    safe_structured,
)
from odyssey.core.logging import get_logger
from odyssey.graph.registry import AgentSpec, register
from odyssey.prompts.agents import SUPPORT_AGENT
from odyssey.providers.llm_provider import get_chat_model
from odyssey.schemas.booking import Booking, BookingStatus, BookingType

log = get_logger(__name__)


class CancelIntent(BaseModel):
    wants_cancel: bool = False
    target: str | None = Field(default=None, description="which booking, e.g. 'hotel', 'flight', or a title")


def _latest_user(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


def _context_summary(state: dict) -> str:
    lines = []
    it = state.get("itinerary") or {}
    if it.get("destination"):
        lines.append(f"Destination: {it['destination']} ({len(it.get('days', []))} days).")
    ctx = state.get("context") or {}
    if ctx.get("overview"):
        lines.append(f"Notes: {ctx['overview']}")
    weather = (ctx.get("weather") or {}).get("days") or []
    if weather:
        lines.append("Weather: " + "; ".join(f"{d['date']} {d['condition']}" for d in weather[:4]))
    confirmed = [b for b in (state.get("confirmed_bookings") or []) if b.get("status") == "confirmed"]
    if confirmed:
        lines.append("Confirmed bookings: " + "; ".join(f"{b['title']} ({b.get('booking_ref')})" for b in confirmed))
    else:
        lines.append("No confirmed bookings yet.")
    return "\n".join(lines)


async def support_node(state: dict) -> dict | Command:
    llm = get_chat_model()
    messages = state.get("messages", [])
    confirmed = [b for b in (state.get("confirmed_bookings") or []) if b.get("status") == "confirmed"]

    # Detect a cancellation request; if so, stage it for the approval gate.
    intent = await safe_structured(
        llm, CancelIntent, [SystemMessage(content="Does the traveler want to cancel a booking?"), HumanMessage(content=_latest_user(messages))], agent=SUPPORT
    )
    if intent and intent.wants_cancel and confirmed:
        target = (intent.target or "").lower().strip()
        matches = [
            b for b in confirmed
            if not target or target in b["title"].lower() or target in str(b.get("type", ""))
        ]
        if matches:
            pending = [
                Booking(
                    type=BookingType(b["type"]),
                    action="cancel",
                    provider=b["provider"],
                    title=b["title"],
                    price=b.get("price", 0.0),
                    currency=b.get("currency", "USD"),
                    status=BookingStatus.pending_approval,
                    booking_ref=b.get("booking_ref"),
                    offer_id=b.get("offer_id"),
                ).model_dump(mode="json")
                for b in matches
            ]
            titles = ", ".join(b["title"] for b in matches)
            return Command(
                goto=BOOKING_CONFIRM,
                update={
                    "pending_bookings": pending,
                    "messages": [AIMessage(content=f"I can cancel {titles}. Please confirm and I'll process it.", name=SUPPORT)],
                    "active_agent": SUPPORT,
                },
            )

    # Otherwise answer the question, grounded in the trip state (streams tokens).
    answer = await llm.ainvoke(
        [SystemMessage(content=SUPPORT_AGENT + "\n\nTrip context:\n" + _context_summary(state)), *messages],
        config=agent_config(SUPPORT),
    )
    content = answer.content if isinstance(answer.content, str) else str(answer.content)
    return Command(
        goto=SUPERVISOR,
        update={"messages": [AIMessage(content=content, name=SUPPORT)], "active_agent": SUPPORT},
    )


register(
    AgentSpec(
        name=SUPPORT,
        description=(
            "24/7 traveler support: answers questions about the trip and bookings, day-of logistics, "
            "and emergencies; handles cancellations through the approval gate. Not for itinerary edits."
        ),
        build=lambda: support_node,
        phase=3,
        dynamic_routing=True,
    )
)
