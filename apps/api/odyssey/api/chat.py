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
    """Resume a graph paused at a human-in-the-loop interrupt with the user's
    decision. Streams the continuation as UIEvents.

    Phase 1 wires the transport; the booking approval node that produces the
    interrupt lands in Phase 3. Until then this returns a no-op stream so the
    frontend contract is stable.
    """
    from langgraph.types import Command

    from odyssey.core.observability import langfuse_config
    from odyssey.graph.stream import _tool_summary  # noqa: F401  (kept for parity)

    runtime = await get_runtime()
    config = {
        "configurable": {"thread_id": session_id},
        **langfuse_config(session_id, user.id),
    }

    async def gen():
        from odyssey.schemas.events import ev_done, ev_error

        try:
            state = await runtime.graph.aget_state(config)
            if not state or not state.next:
                # nothing is interrupted; contract-safe no-op
                yield ev_done(session_id).sse()
                return
            resume_value = {"approved": body.approved, "note": body.note, "booking_id": body.booking_id}
            async for _ in runtime.graph.astream(Command(resume=resume_value), config=config):
                pass
            yield ev_done(session_id).sse()
        except Exception as e:  # pragma: no cover
            log.exception("resume.error", session_id=session_id)
            yield ev_error(None, f"Resume failed: {e}").sse()

    return EventSourceResponse(gen())
