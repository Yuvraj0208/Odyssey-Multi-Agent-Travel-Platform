"""Prometheus metrics and per-session telemetry accounting.

Metrics are exposed at GET /metrics. The SessionTelemetry accumulator is the
source of truth the UI mission-control panel reads for tokens / cost / latency;
it is fed from LangGraph events and (when enabled) reconciled against Langfuse.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

REGISTRY = CollectorRegistry()

HTTP_REQUESTS = Counter(
    "odyssey_http_requests_total",
    "HTTP requests",
    ["method", "path", "status"],
    registry=REGISTRY,
)
HTTP_LATENCY = Histogram(
    "odyssey_http_request_seconds",
    "HTTP request latency",
    ["method", "path"],
    registry=REGISTRY,
)
AGENT_STEPS = Counter(
    "odyssey_agent_steps_total",
    "Agent node executions",
    ["agent"],
    registry=REGISTRY,
)
TOOL_CALLS = Counter(
    "odyssey_tool_calls_total",
    "Tool invocations",
    ["tool", "outcome"],
    registry=REGISTRY,
)
TOOL_LATENCY = Histogram(
    "odyssey_tool_seconds",
    "Tool call latency",
    ["tool"],
    registry=REGISTRY,
)
LLM_TOKENS = Counter(
    "odyssey_llm_tokens_total",
    "LLM tokens",
    ["direction", "model"],
    registry=REGISTRY,
)


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


# Rough per-1M-token USD pricing for cost estimation in the UI. Groq open models
# are effectively free on the dev tier; these are order-of-magnitude estimates so
# the telemetry readout shows a real (non-fabricated) computed number.
_PRICE_PER_MTOK = {
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "llama-3.1-8b-instant": (0.05, 0.08),
    "default": (0.30, 0.40),
}


@dataclass
class SessionTelemetry:
    """Per-session running totals surfaced to the mission-control panel."""

    session_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "default"
    started_at: float = field(default_factory=time.perf_counter)
    last_latency_ms: float = 0.0
    tool_calls: int = 0
    agent_steps: int = 0

    def add_usage(self, input_tokens: int, output_tokens: int, model: str | None = None) -> None:
        self.input_tokens += max(0, input_tokens)
        self.output_tokens += max(0, output_tokens)
        if model:
            self.model = model
            LLM_TOKENS.labels("input", model).inc(max(0, input_tokens))
            LLM_TOKENS.labels("output", model).inc(max(0, output_tokens))

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        pin, pout = _PRICE_PER_MTOK.get(self.model, _PRICE_PER_MTOK["default"])
        return (self.input_tokens / 1_000_000 * pin) + (self.output_tokens / 1_000_000 * pout)

    def snapshot(self) -> dict:
        return {
            "session_id": self.session_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "model": self.model,
            "tool_calls": self.tool_calls,
            "agent_steps": self.agent_steps,
            "last_latency_ms": round(self.last_latency_ms, 1),
        }


# In-memory registry of live sessions. In stack mode this can be backed by Redis;
# the interface is the same.
_SESSIONS: dict[str, SessionTelemetry] = {}


def get_session_telemetry(session_id: str) -> SessionTelemetry:
    tel = _SESSIONS.get(session_id)
    if tel is None:
        tel = SessionTelemetry(session_id=session_id)
        _SESSIONS[session_id] = tel
    return tel
