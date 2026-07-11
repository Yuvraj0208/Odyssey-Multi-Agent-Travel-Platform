"""Chat streaming + resume endpoints.

POST /chat/{session_id}/stream runs one turn and streams UIEvents over SSE. The
same feed drives the transcript and the mission-control panel. POST
/chat/{session_id}/resume injects a human-in-the-loop decision and continues the
graph past an interrupt (used by the booking approval flow in Phase 3+).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from odyssey.api.deps import CurrentUser, current_user
from odyssey.core.logging import get_logger
from odyssey.graph.runtime import get_runtime
from odyssey.graph.stream import stream_turn
from odyssey.schemas.chat import ChatIn, ResumeIn

router = APIRouter(tags=["chat"])
log = get_logger(__name__)


@router.post("/chat/{session_id}/stream")
async def chat_stream(
    session_id: str, body: ChatIn, user: CurrentUser = Depends(current_user)
):
    runtime = await get_runtime()

    async def gen():
        async for ui in stream_turn(runtime, user.id, session_id, body.text):
            yield ui.sse()

    return EventSourceResponse(gen())


@router.post("/chat/{session_id}/resume")
async def chat_resume(
    session_id: str, body: ResumeIn, user: CurrentUser = Depends(current_user)
):
    """Resume a graph paused at the human-in-the-loop approval gate with the user's
    decision, streaming the continuation (confirmations + wrap-up) as UIEvents."""
    from odyssey.graph.stream import resume_turn
    from odyssey.schemas.events import ev_done, ev_error

    runtime = await get_runtime()
    decision = {"approved": body.approved, "note": body.note, "booking_id": body.booking_id}

    async def gen():
        try:
            snapshot = await runtime.graph.aget_state(
                {"configurable": {"thread_id": session_id}}
            )
            interrupted = bool(snapshot and getattr(snapshot, "interrupts", None))
            if not interrupted:
                yield ev_done(session_id).sse()  # contract-safe no-op
                return
            async for ui in resume_turn(runtime, user.id, session_id, decision):
                yield ui.sse()
        except Exception as e:  # pragma: no cover
            log.exception("resume.error", session_id=session_id)
            yield ev_error(None, f"Resume failed: {e}").sse()

    return EventSourceResponse(gen())
