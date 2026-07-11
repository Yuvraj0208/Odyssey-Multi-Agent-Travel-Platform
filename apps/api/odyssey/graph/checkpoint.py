"""Checkpointer + long-term store factories, mode-aware.

  local: AsyncSqliteSaver (persists to a file so resume-after-restart works) +
         in-process InMemoryStore.
  stack: AsyncPostgresSaver + AsyncPostgresStore (durable, multi-process).

Each factory returns (component, aclose) so the runtime can manage lifecycle.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from odyssey.core.config import Settings
from odyssey.core.logging import get_logger

log = get_logger(__name__)

Closer = Callable[[], Awaitable[None]]


async def _noop() -> None:
    return None


async def make_checkpointer(settings: Settings) -> tuple[Any, Closer]:
    if settings.is_local:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        path = settings.resolve_path(settings.checkpoint_sqlite_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cm = AsyncSqliteSaver.from_conn_string(str(path))
        saver = await cm.__aenter__()
        await saver.setup()
        log.info("checkpointer.sqlite", path=str(path))

        async def close() -> None:
            await cm.__aexit__(None, None, None)

        return saver, close

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    cm = AsyncPostgresSaver.from_conn_string(settings.database_url.replace("+psycopg", ""))
    saver = await cm.__aenter__()
    await saver.setup()
    log.info("checkpointer.postgres")

    async def close() -> None:
        await cm.__aexit__(None, None, None)

    return saver, close


async def make_store(settings: Settings) -> tuple[Any, Closer]:
    if settings.is_local:
        from langgraph.store.memory import InMemoryStore

        log.info("store.memory")
        return InMemoryStore(), _noop

    from langgraph.store.postgres.aio import AsyncPostgresStore

    cm = AsyncPostgresStore.from_conn_string(settings.database_url.replace("+psycopg", ""))
    store = await cm.__aenter__()
    await store.setup()
    log.info("store.postgres")

    async def close() -> None:
        await cm.__aexit__(None, None, None)

    return store, close
