"""TravelState - the single shared, typed contract every agent reads and writes.

Reducers keep concurrent updates merging cleanly instead of clobbering:
  - messages: add_messages (append + de-dup by id)
  - tool_events, errors: append-only lists
Everything else is last-writer-wins, which is safe because the supervisor
serializes who holds the turn.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def _merge_dict(left: dict | None, right: dict | None) -> dict:
    """Shallow-merge reducer for the cross-agent scratchpad."""
    out = dict(left or {})
    out.update(right or {})
    return out


class TravelState(TypedDict, total=False):
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]

    # Identity / routing
    user_id: str
    session_id: str
    active_agent: str
    next_agent: str | None
    hops: int  # guard against runaway supervisor loops

    # Trip artifacts
    trip_brief: dict | None
    itinerary: dict | None
    options: dict
    pending_bookings: list[dict]
    confirmed_bookings: list[dict]

    # Cross-agent scratchpad (weather, pois, overview, preferences)
    context: Annotated[dict, _merge_dict]

    # Append-only feeds
    tool_events: Annotated[list[dict], operator.add]
    errors: Annotated[list[dict], operator.add]


def turn_input(user_id: str, session_id: str, text: str) -> dict[str, Any]:
    """Minimal per-turn input. Persistent collections (itinerary, options, bookings,
    research context) are intentionally omitted so the checkpointer's values survive
    a resume; only the new message and per-turn routing counters are (re)set here."""
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=text)],
        "user_id": user_id,
        "session_id": session_id,
        "active_agent": "supervisor",
        "next_agent": None,
        "hops": 0,
    }
