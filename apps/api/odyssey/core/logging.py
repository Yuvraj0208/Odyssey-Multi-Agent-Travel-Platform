"""Structured logging via structlog.

JSON logs in production, pretty console logs in dev. A contextvar carries a
request/session correlation id so every log line inside a request can be tied
together (and to the Langfuse trace).
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

# Correlation id bound per request/session; included in every log line.
correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def _add_correlation_id(_logger, _name, event_dict):
    cid = correlation_id.get()
    if cid:
        event_dict["cid"] = cid
    return event_dict


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """Configure structlog + stdlib logging once at startup."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_correlation_id,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, httpx) through the same stream at WARNING+.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.WARNING,
    )


def get_logger(name: str = "odyssey") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
