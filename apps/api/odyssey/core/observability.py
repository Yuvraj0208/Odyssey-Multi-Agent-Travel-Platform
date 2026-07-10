"""Langfuse tracing wiring.

If LANGFUSE_ENABLED is true and the SDK is installed, we return a callback handler
that is attached to every LangGraph invocation so each agent step, tool call,
token count, latency, and cost is captured. If disabled or unavailable, callbacks
are simply empty and the app runs unchanged. Never a hard dependency on the run path.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from odyssey.core.config import get_settings
from odyssey.core.logging import get_logger

log = get_logger(__name__)


@lru_cache
def _handler() -> Any | None:
    s = get_settings()
    if not s.langfuse_enabled:
        return None
    try:
        from langfuse.callback import CallbackHandler
    except ImportError:
        log.warning("langfuse.unavailable", reason="langfuse not installed; tracing disabled")
        return None
    try:
        handler = CallbackHandler(
            public_key=s.langfuse_public_key,
            secret_key=s.langfuse_secret_key,
            host=s.langfuse_host,
        )
        log.info("langfuse.enabled", host=s.langfuse_host)
        return handler
    except Exception as e:  # pragma: no cover - defensive
        log.warning("langfuse.init_failed", error=str(e))
        return None


def langfuse_callbacks(session_id: str | None = None, user_id: str | None = None) -> list[Any]:
    """Return the callback list to pass into graph config['callbacks']."""
    h = _handler()
    return [h] if h is not None else []


def langfuse_config(session_id: str, user_id: str) -> dict:
    """Config fragment (callbacks + metadata) merged into the graph run config."""
    cbs = langfuse_callbacks(session_id, user_id)
    if not cbs:
        return {}
    return {
        "callbacks": cbs,
        "metadata": {
            "langfuse_session_id": session_id,
            "langfuse_user_id": user_id,
        },
    }
