"""Shared async HTTP client with timeout, retry, and a light circuit breaker.

Every external tool goes through here so degradation is uniform: transient errors
retry with backoff, repeated failures trip a per-host breaker (fail fast), and the
caller gets a typed ToolError it can turn into a graceful fallback.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from odyssey.core.logging import get_logger

log = get_logger(__name__)


class ToolError(RuntimeError):
    """Raised when an external call fails after retries or the breaker is open."""


# Several open endpoints (Nominatim, Overpass) reject the default python-httpx
# User-Agent, so we identify the app on every request.
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OdysseyTravel/0.1; +https://odyssey.local)",
    "Accept": "application/json",
}


@dataclass
class _Breaker:
    fail_threshold: int = 4
    reset_after_s: float = 30.0
    failures: int = 0
    opened_at: float = 0.0

    def allow(self) -> bool:
        if self.failures < self.fail_threshold:
            return True
        if time.monotonic() - self.opened_at > self.reset_after_s:
            self.failures = 0  # half-open: let one through
            return True
        return False

    def record_success(self) -> None:
        self.failures = 0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.fail_threshold:
            self.opened_at = time.monotonic()


@dataclass
class HttpClient:
    timeout_s: float = 12.0
    _breakers: dict[str, _Breaker] = field(default_factory=dict)

    def _breaker(self, host: str) -> _Breaker:
        return self._breakers.setdefault(host, _Breaker())

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.4, max=4),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    )
    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        headers = {**DEFAULT_HEADERS, **(kwargs.pop("headers", None) or {})}
        async with httpx.AsyncClient(timeout=self.timeout_s, follow_redirects=True) as c:
            resp = await c.request(method, url, headers=headers, **kwargs)
            resp.raise_for_status()
            return resp

    async def _guarded(self, method: str, url: str, host: str, **kwargs) -> httpx.Response:
        br = self._breaker(host)
        if not br.allow():
            raise ToolError(f"circuit open for {host}")
        try:
            resp = await self._request(method, url, **kwargs)
            br.record_success()
            return resp
        except Exception as e:
            br.record_failure()
            log.warning("http.error", host=host, url=url, error=str(e))
            raise ToolError(f"{host} request failed: {e}") from e

    async def get_json(self, url: str, *, host: str, **kwargs):
        resp = await self._guarded("GET", url, host, **kwargs)
        return resp.json()

    async def post_json(self, url: str, *, host: str, **kwargs):
        resp = await self._guarded("POST", url, host, **kwargs)
        return resp.json()

    async def post_text(self, url: str, *, host: str, **kwargs) -> str:
        resp = await self._guarded("POST", url, host, **kwargs)
        return resp.text


# Process-wide client so breakers are shared.
http_client = HttpClient()
