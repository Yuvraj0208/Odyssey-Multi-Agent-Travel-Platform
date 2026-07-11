"""Booking agent + human-in-the-loop approval gate.

Flow:
  booking (search + price + stage pending_bookings)
    -> booking_confirm (interrupt for approval)
       -> on approve: confirm each with idempotency keys -> confirmed_bookings
       -> on decline: clear pending, no charge
    -> supervisor

Nothing is ever confirmed without the explicit approval that clears the interrupt.
Splitting search and confirm into two nodes means the staged bookings are committed
to state before the pause, so a resume re-runs only the confirm step.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

from odyssey.agents.base import (
    BOOKING,
    BOOKING_CONFIRM,
    SUPERVISOR,
    agent_config,
    error_event,
    safe_structured,
)
from odyssey.core.logging import get_logger
from odyssey.graph.registry import AgentSpec, register
from odyssey.prompts.agents import BOOKING_INTENT
from odyssey.providers.booking.tools import cancel_offer, confirm_offer, search_offers
from odyssey.providers.llm_provider import get_chat_model
from odyssey.schemas.booking import Booking, BookingStatus, BookingType

log = get_logger(__name__)


class BookingIntent(BaseModel):
    book_flights: bool = False
    book_hotel: bool = False
    book_activities: bool = False
    origin: str | None = Field(default=None, description="departure city/airport for flights, if stated")


def _latest_user(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


def _trip_params(brief: dict, itinerary: dict, ctx: dict) -> dict:
    dest = brief.get("destination") or itinerary.get("destination")
    center = itinerary.get("center") or ctx.get("destination") or {}
    return {
        "dest": dest,
        "start": brief.get("start_date"),
        "end": brief.get("end_date"),
        "nights": max(1, len(itinerary.get("days", [])) or brief.get("duration_days") or 3),
        "pax": max(1, (brief.get("party") or {}).get("adults", 1)),
        "lat": center.get("lat"),
        "lng": center.get("lng"),
        "interests": brief.get("interests") or [],
    }


def _booking_from_priced(priced: dict) -> Booking:
    return Booking(
        type=BookingType(priced["type"]),
        provider=priced["provider"],
        title=priced["title"],
        price=priced["price"],
        currency=priced.get("currency", "USD"),
        offer_id=priced.get("offer_id"),
        cancellation=priced.get("cancellation", "See provider terms"),
        status=BookingStatus.pending_approval,
        details=priced,
    )


async def _search(category: str, **kwargs) -> dict:
    msg = await search_offers.ainvoke(
        {"type": "tool_call", "id": f"s_{category}", "name": "search_offers", "args": {"category": category, **kwargs}},
        config=agent_config(BOOKING),
    )
    return getattr(msg, "artifact", {}) or {}


async def booking_node(state: dict) -> dict | Command:
    brief = state.get("trip_brief") or {}
    itinerary = state.get("itinerary")
    ctx = state.get("context") or {}
    messages = state.get("messages", [])

    if not itinerary:
        return Command(
            goto=SUPERVISOR,
            update={
                "messages": [AIMessage(content="I can book flights, hotels, and activities once we have an itinerary. Shall I plan the trip first?", name=BOOKING)],
                "active_agent": BOOKING,
            },
        )

    intent = await safe_structured(
        get_chat_model(),
        BookingIntent,
        [SystemMessage(content=BOOKING_INTENT), HumanMessage(content=_latest_user(messages))],
        agent=BOOKING,
    ) or BookingIntent()

    p = _trip_params(brief, itinerary, ctx)
    origin = intent.origin or brief.get("origin")
    if not (intent.book_flights or intent.book_hotel or intent.book_activities):
        intent.book_hotel = True
        intent.book_flights = bool(origin)

    options: dict = {}
    staged: list[Booking] = []

    if intent.book_flights and origin:
        art = await _search("flight", destination=p["dest"], origin=origin, depart_date=p["start"], return_date=p["end"], passengers=p["pax"])
        if art.get("offers"):
            options["flights"] = art["offers"]
        if art.get("priced_top"):
            staged.append(_booking_from_priced(art["priced_top"]))

    if intent.book_hotel:
        art = await _search("hotel", destination=p["dest"], depart_date=p["start"], return_date=p["end"], nights=p["nights"], lat=p["lat"], lng=p["lng"])
        if art.get("offers"):
            options["hotels"] = art["offers"]
        if art.get("priced_top"):
            staged.append(_booking_from_priced(art["priced_top"]))

    if intent.book_activities:
        art = await _search("activity", destination=p["dest"], interests=p["interests"], lat=p["lat"], lng=p["lng"], depart_date=p["start"])
        if art.get("offers"):
            options["activities"] = art["offers"]
        if art.get("priced_top"):
            staged.append(_booking_from_priced(art["priced_top"]))

    if not staged:
        hint = " I need a departure city to price flights." if intent.book_flights and not origin else ""
        return Command(
            goto=SUPERVISOR,
            update={
                "options": options,
                "messages": [AIMessage(content=f"I couldn't find anything to book right now.{hint}", name=BOOKING)],
                "active_agent": BOOKING,
            },
        )

    total = round(sum(b.price for b in staged), 2)
    lines = "\n".join(f"- {b.title} ({b.provider}) - ${b.price:.0f}, {b.cancellation}" for b in staged)
    msg = (
        f"Here's what I can book for your approval:\n{lines}\n\n"
        f"Estimated total ${total:.0f}. Nothing is charged until you approve."
    )
    return Command(
        goto=BOOKING_CONFIRM,
        update={
            "options": options,
            "pending_bookings": [b.model_dump(mode="json") for b in staged],
            "messages": [AIMessage(content=msg, name=BOOKING)],
            "active_agent": BOOKING,
        },
    )


async def _confirm(b: dict) -> dict:
    msg = await confirm_offer.ainvoke(
        {
            "type": "tool_call",
            "id": f"c_{b['id']}",
            "name": "confirm_offer",
            "args": {
                "provider": b["provider"],
                "offer_id": b.get("offer_id") or "",
                "type": b["type"],
                "title": b["title"],
                "price": b["price"],
                "currency": b.get("currency", "USD"),
                "idempotency_key": b["idempotency_key"],
            },
        },
        config=agent_config(BOOKING),
    )
    return getattr(msg, "artifact", {}) or {}


async def _cancel(b: dict) -> dict:
    msg = await cancel_offer.ainvoke(
        {"type": "tool_call", "id": f"x_{b['id']}", "name": "cancel_offer",
         "args": {"provider": b["provider"], "booking_ref": b.get("booking_ref") or ""}},
        config=agent_config(BOOKING),
    )
    return getattr(msg, "artifact", {}) or {}


async def booking_confirm_node(state: dict) -> Command:
    pending = state.get("pending_bookings") or []
    if not pending:
        return Command(goto=SUPERVISOR, update={"active_agent": BOOKING_CONFIRM})

    total = round(sum(b.get("price", 0) for b in pending), 2)
    # PAUSE for explicit human approval. Resumes with the user's decision dict.
    decision = interrupt(
        {
            "kind": "booking_approval",
            "bookings": pending,
            "total": total,
            "currency": pending[0].get("currency", "USD"),
        }
    )
    approved = decision.get("approved", False) if isinstance(decision, dict) else bool(decision)
    is_cancel = all(b.get("action") == "cancel" for b in pending)

    if not approved:
        verb = "cancelled anything" if is_cancel else "booked anything"
        return Command(
            goto=SUPERVISOR,
            update={
                "pending_bookings": [],
                "messages": [AIMessage(content=f"No problem - I haven't {verb}. Let me know if you'd like to adjust.", name=BOOKING)],
                "active_agent": BOOKING_CONFIRM,
            },
        )

    # confirmed_bookings is managed as the full list so cancellations can update status.
    booked = list(state.get("confirmed_bookings") or [])
    confirmed_titles: list[str] = []
    cancelled_titles: list[str] = []
    failed: list[str] = []
    errors: list[dict] = []

    for b in pending:
        if b.get("action") == "cancel":
            await _cancel(b)
            for e in booked:
                if e.get("booking_ref") and e["booking_ref"] == b.get("booking_ref"):
                    e["status"] = "cancelled"
            cancelled_titles.append(b["title"])
        else:
            art = await _confirm(b)
            if art.get("error") or art.get("status") == "failed":
                failed.append(b["title"])
                errors.append(error_event(BOOKING, f"booking failed: {b['title']}", "left unbooked"))
            else:
                booked.append({**b, "status": "confirmed", "booking_ref": art.get("booking_ref")})
                confirmed_titles.append(f"{b['title']} ({art.get('booking_ref')})")

    parts = []
    if confirmed_titles:
        parts.append(f"Confirmed: {'; '.join(confirmed_titles)}.")
    if cancelled_titles:
        parts.append(f"Cancelled: {', '.join(cancelled_titles)}.")
    if failed:
        parts.append(f"Could not book: {', '.join(failed)} - you can retry those.")
    note = " ".join(parts) or "Nothing was changed."

    return Command(
        goto=SUPERVISOR,
        update={
            "confirmed_bookings": booked,
            "pending_bookings": [],
            "errors": errors,
            "messages": [AIMessage(content=note, name=BOOKING)],
            "active_agent": BOOKING_CONFIRM,
        },
    )


register(
    AgentSpec(
        name=BOOKING,
        description=(
            "Searches and prices flights, hotels, and activities across providers, then stages them "
            "for explicit approval before booking. Use when the traveler asks to book or reserve anything."
        ),
        build=lambda: booking_node,
        phase=3,
        dynamic_routing=True,
    )
)
