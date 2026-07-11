"""Process-wide graph runtime.

Builds the compiled graph + checkpointer + store once, lazily on first use (guarded
by a lock), and exposes them to the API layer. Also owns clean shutdown so the
SQLite/Postgres connections close.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from odyssey.core.config import get_settings
from odyssey.core.logging import get_logger
from odyssey.graph.build import build_graph
from odyssey.graph.checkpoint import Closer, make_checkpointer, make_store

log = get_logger(__name__)


@dataclass
class GraphRuntime:
    graph: Any
    checkpointer: Any
    store: Any
    _closers: list[Closer]

    async def aclose(self) -> None:
        for c in reversed(self._closers):
            try:
                await c()
            except Exception as e:  # pragma: no cover
                log.warning("runtime.close_error", error=str(e))


_runtime: GraphRuntime | None = None
_lock = asyncio.Lock()


async def get_runtime() -> GraphRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    async with _lock:
        if _runtime is not None:
            return _runtime
        s = get_settings()
        checkpointer, close_cp = await make_checkpointer(s)
        store, close_store = await make_store(s)
        graph = build_graph(checkpointer, store)
        _runtime = GraphRuntime(
            graph=graph,
            checkpointer=checkpointer,
            store=store,
            _closers=[close_cp, close_store],
        )
        log.info("runtime.ready", mode=s.mode)
        return _runtime


async def shutdown_runtime() -> None:
    global _runtime
    if _runtime is not None:
        await _runtime.aclose()
        _runtime = None
