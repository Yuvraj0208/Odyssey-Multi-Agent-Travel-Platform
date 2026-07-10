"""Health, readiness, and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response

from odyssey import __version__
from odyssey.core.config import get_settings
from odyssey.core.telemetry import metrics_response
from odyssey.providers.llm_provider import llm_health

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health() -> dict:
    """Liveness: the process is up. Never touches external services."""
    s = get_settings()
    return {"status": "ok", "version": __version__, "mode": s.mode, "env": s.env}


@router.get("/ready")
async def ready() -> dict:
    """Readiness: config is valid and the LLM provider is configured.

    In stack mode this is where DB/redis/qdrant pings are added; in local mode we
    report the LLM configuration so the UI can warn if no key is set yet.
    """
    s = get_settings()
    llm = llm_health()
    ready = llm["configured"]
    return {
        "ready": ready,
        "mode": s.mode,
        "llm": llm,
        "vector_backend": s.vector_backend,
        "langfuse": s.langfuse_enabled,
    }


@router.get("/metrics")
async def metrics() -> Response:
    body, content_type = metrics_response()
    return Response(content=body, media_type=content_type)
