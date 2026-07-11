"""Event bus for proactive, event-driven flows (re-planning notifications).

  local: in-process asyncio pub/sub (no dependencies).
  stack: Redis pub/sub (same interface).

Publishers (e.g. the conditions monitor) emit on a channel; subscribers (the
re-planning coordinator, the notifications SSE endpoint) consume. This is what
makes proactive re-planning event-driven rather than request-response.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Protocol

import orjson

from odyssey.core.config import get_settings
from odyssey.core.logging import get_logger

log = get_logger(__name__)

# Well-known channels
CH_WEATHER_CHANGED = "weather_changed"


def ch_notify(user_id: str) -> str:
    return f"notify:{user_id}"


class EventBus(Protocol):
    async def publish(self, channel: str, payload: dict) -> None: ...
    def subscribe(self, channel: str) -> AsyncIterator[dict]: ...
    async def aclose(self) -> None: ...


class InProcessEventBus:
    """Single-process pub/sub via per-subscriber asyncio queues."""

    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue]] = {}

    async def publish(self, channel: str, payload: dict) -> None:
        for q in list(self._subs.get(channel, ())):
            q.put_nowait(payload)

    async def subscribe(self, channel: str) -> AsyncIterator[dict]:
        q: asyncio.Queue = asyncio.Queue()
        self._subs.setdefault(channel, set()).add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subs.get(channel, set()).discard(q)

    async def aclose(self) -> None:
        self._subs.clear()


class RedisEventBus:
    """Redis pub/sub (stack mode). Same interface as the in-process bus."""

    def __init__(self, url: str) -> None:
        import redis.asyncio as redis

        self._redis = redis.from_url(url, decode_responses=True)

    async def publish(self, channel: str, payload: dict) -> None:
        await self._redis.publish(channel, orjson.dumps(payload).decode())

    async def subscribe(self, channel: str) -> AsyncIterator[dict]:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for msg in pubsub.listen():
                if msg.get("type") == "message":
                    yield orjson.loads(msg["data"])
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    async def aclose(self) -> None:
        await self._redis.aclose()


_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is not None:
        return _bus
    s = get_settings()
    if s.is_local:
        _bus = InProcessEventBus()
        log.info("eventbus.inprocess")
    else:
        try:
            _bus = RedisEventBus(s.redis_url)
            log.info("eventbus.redis")
        except Exception as e:  # pragma: no cover - fall back so the app still runs
            log.warning("eventbus.redis_failed", error=str(e))
            _bus = InProcessEventBus()
    return _bus


async def shutdown_event_bus() -> None:
    global _bus
    if _bus is not None:
        await _bus.aclose()
        _bus = None
