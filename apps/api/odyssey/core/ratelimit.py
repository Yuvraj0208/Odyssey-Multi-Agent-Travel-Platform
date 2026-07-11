"""Token-bucket rate limiting, per user/IP.

In-process (local) by default; the same interface can be backed by a Redis token
bucket in stack mode for multi-process coordination. Applied as middleware to the
API surface, skipping health/metrics.
"""

from __future__ import annotations

import time

from odyssey.core.config import get_settings


class TokenBucket:
    def __init__(self, per_minute: int) -> None:
        self.capacity = max(1, per_minute)
        self.rate = self.capacity / 60.0  # tokens per second
        self._buckets: dict[str, tuple[float, float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        tokens, last = self._buckets.get(key, (float(self.capacity), now))
        tokens = min(self.capacity, tokens + (now - last) * self.rate)
        if tokens >= 1.0:
            self._buckets[key] = (tokens - 1.0, now)
            return True
        self._buckets[key] = (tokens, now)
        return False


_limiter: TokenBucket | None = None


def get_limiter() -> TokenBucket:
    global _limiter
    if _limiter is None:
        _limiter = TokenBucket(get_settings().rate_limit_per_minute)
    return _limiter


def client_key(request) -> str:
    uid = request.headers.get("x-user-id")
    if uid:
        return f"user:{uid}"
    auth = request.headers.get("authorization", "")
    if auth:
        return f"auth:{hash(auth) & 0xffffffff}"
    client = request.client
    return f"ip:{client.host if client else 'unknown'}"
