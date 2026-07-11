"""Odyssey FastAPI application entrypoint.

Wires config, structured logging, metrics, CORS, and routers. The multi-agent
graph is built lazily on first use (see odyssey.graph.runtime) so the app boots
instantly and health checks never depend on the LLM.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from odyssey import __version__
from odyssey.api import health
from odyssey.core.config import get_settings
from odyssey.core.logging import configure_logging, correlation_id, get_logger
from odyssey.core.telemetry import HTTP_LATENCY, HTTP_REQUESTS

log = get_logger("odyssey.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    configure_logging(level=s.log_level, json_logs=s.log_json)
    log.info(
        "startup",
        version=__version__,
        mode=s.mode,
        env=s.env,
        llm_provider=s.llm_provider,
        llm_model=s.llm_model,
        llm_configured=s.llm_configured,
        vector_backend=s.vector_backend,
    )
    # Start event-driven proactive coordinators (weather re-planning notifications).
    from odyssey.core.notifications import start_proactive_coordinators

    start_proactive_coordinators()
    yield
    from odyssey.core.events import shutdown_event_bus
    from odyssey.core.notifications import stop_proactive_coordinators
    from odyssey.graph.runtime import shutdown_runtime

    await stop_proactive_coordinators()
    await shutdown_event_bus()
    await shutdown_runtime()
    log.info("shutdown")


def create_app() -> FastAPI:
    s = get_settings()
    configure_logging(level=s.log_level, json_logs=s.log_json)

    app = FastAPI(
        title="Odyssey API",
        version=__version__,
        description="Agentic AI travel platform - LangGraph multi-agent core.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def observability_mw(request: Request, call_next):
        cid = request.headers.get("x-correlation-id") or uuid.uuid4().hex[:12]
        token = correlation_id.set(cid)
        start = time.perf_counter()
        path = request.url.path
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            HTTP_REQUESTS.labels(request.method, path, "500").inc()
            log.exception("request.error", method=request.method, path=path)
            raise
        finally:
            correlation_id.reset(token)
        elapsed = time.perf_counter() - start
        HTTP_LATENCY.labels(request.method, path).observe(elapsed)
        HTTP_REQUESTS.labels(request.method, path, str(status)).inc()
        response.headers["x-correlation-id"] = cid
        log.info(
            "request",
            method=request.method,
            path=path,
            status=status,
            ms=round(elapsed * 1000, 1),
        )
        return response

    # Routers
    app.include_router(health.router)

    from odyssey.api import meta as meta_router

    app.include_router(meta_router.router, prefix="/api")

    # Feature routers are registered here as phases land. Import guarded so the
    # app still boots if an optional dependency for a later phase is absent.
    try:
        from odyssey.api import chat as chat_router

        app.include_router(chat_router.router, prefix="/api")
    except Exception as e:  # pragma: no cover - defensive during phased build
        log.warning("router.chat.skipped", error=str(e))

    try:
        from odyssey.api import sessions as sessions_router

        app.include_router(sessions_router.router, prefix="/api")
    except Exception as e:  # pragma: no cover
        log.warning("router.sessions.skipped", error=str(e))

    try:
        from odyssey.api import notifications as notifications_router

        app.include_router(notifications_router.router, prefix="/api")
    except Exception as e:  # pragma: no cover
        log.warning("router.notifications.skipped", error=str(e))

    try:
        from odyssey.api import memory as memory_router

        app.include_router(memory_router.router, prefix="/api")
    except Exception as e:  # pragma: no cover
        log.warning("router.memory.skipped", error=str(e))

    return app


app = create_app()
