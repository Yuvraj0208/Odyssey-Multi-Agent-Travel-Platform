"""Session lifecycle + state rehydration.

Sessions are LangGraph threads (thread_id == session_id). The checkpointer is the
source of truth, so GET /sessions/{id}/state rebuilds the transcript, itinerary,
and live agent context after a page reload or a server restart - this is what makes
conversations durable and resumable.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from odyssey.api.deps import CurrentUser, current_user
from odyssey.core.telemetry import get_session_telemetry
from odyssey.graph.runtime import get_runtime
from odyssey.schemas.chat import SessionOut

router = APIRouter(tags=["sessions"])


class ReorderIn(BaseModel):
    itinerary: dict


@router.post("/sessions", response_model=SessionOut)
async def create_session(user: CurrentUser = Depends(current_user)) -> SessionOut:
    return SessionOut(session_id=uuid.uuid4().hex, user_id=user.id, status="active")


@router.get("/sessions")
async def list_sessions(user: CurrentUser = Depends(current_user)) -> dict:
    from odyssey.memory.store_repo import list_sessions as _list

    runtime = await get_runtime()
    return {"sessions": await _list(runtime.store, user.id)}


@router.post("/sessions/{session_id}/reorder")
async def reorder_itinerary(
    session_id: str, body: ReorderIn, user: CurrentUser = Depends(current_user)
) -> dict:
    """Persist a drag-reordered itinerary and re-validate day-of timing (logistics),
    deterministically (no LLM) so the timeline updates instantly."""
    from odyssey.agents.logistics import revalidate_itinerary

    runtime = await get_runtime()
    itinerary = body.itinerary
    await revalidate_itinerary(itinerary)  # recompute transit + feasibility
    await runtime.graph.aupdate_state(
        {"configurable": {"thread_id": session_id}},
        {"itinerary": itinerary, "context": {"logistics_done": True}},
    )
    return {"itinerary": itinerary}


@router.get("/sessions/{session_id}/state")
async def get_session_state(session_id: str, user: CurrentUser = Depends(current_user)) -> dict:
    runtime = await get_runtime()
    config = {"configurable": {"thread_id": session_id}}
    snapshot = await runtime.graph.aget_state(config)
    values = (snapshot.values if snapshot else {}) or {}

    transcript = []
    for m in values.get("messages", []) or []:
        if isinstance(m, HumanMessage):
            role = "user"
        elif isinstance(m, AIMessage):
            role = "assistant"
        else:
            continue
        content = m.content if isinstance(m.content, str) else str(m.content)
        if not content.strip():
            continue
        transcript.append({"role": role, "agent": getattr(m, "name", None), "text": content})

    return {
        "session_id": session_id,
        "user_id": user.id,
        "exists": bool(snapshot and snapshot.values),
        "transcript": transcript,
        "itinerary": values.get("itinerary"),
        "trip_brief": values.get("trip_brief"),
        "tool_events": values.get("tool_events", []),
        "errors": values.get("errors", []),
        "telemetry": get_session_telemetry(session_id).snapshot(),
        "interrupted": bool(snapshot and getattr(snapshot, "interrupts", None)),
        "pending_bookings": values.get("pending_bookings", []),
        "confirmed_bookings": values.get("confirmed_bookings", []),
    }


@router.post("/sessions/{session_id}/recheck")
async def recheck_conditions(
    session_id: str, demo: bool = False, user: CurrentUser = Depends(current_user)
) -> dict:
    """Re-evaluate live conditions (weather) against the saved itinerary and publish
    proactive notifications for any newly adverse outdoor days. Pass ?demo=true to
    exercise the full event path when live weather is benign."""
    from odyssey.proactive.monitor import check_conditions

    runtime = await get_runtime()
    snapshot = await runtime.graph.aget_state({"configurable": {"thread_id": session_id}})
    values = (snapshot.values if snapshot else {}) or {}
    if not values.get("itinerary"):
        return {"issues": 0, "detail": "no itinerary yet"}
    values = {**values, "user_id": user.id, "session_id": session_id}
    issues = await check_conditions(values, publish=True, force_demo=demo)
    return {"issues": len(issues), "days": [i["day"] for i in issues]}
