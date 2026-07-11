"""Agent registry - the loose-coupling seam.

Each agent module defines an AgentSpec and calls register(...). The supervisor's
routing prompt is assembled from these descriptions at runtime, so adding an agent
never requires editing the supervisor or peers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# build() returns a graph node: either a compiled subgraph or an async callable
# (state) -> dict | Command. Kept as Any so specialists can choose either form.
NodeBuilder = Callable[..., Any]


@dataclass
class AgentSpec:
    name: str
    description: str  # supervisor uses this text to decide routing
    build: NodeBuilder
    # Phase in which the agent becomes active; lets us light up future nodes in the
    # mission-control UI without routing to them yet.
    phase: int = 1
    tags: list[str] = field(default_factory=list)


AGENT_REGISTRY: dict[str, AgentSpec] = {}


def register(spec: AgentSpec) -> None:
    AGENT_REGISTRY[spec.name] = spec


def clear_registry() -> None:
    AGENT_REGISTRY.clear()


def registry_descriptions() -> str:
    """Formatted agent menu for the supervisor prompt."""
    lines = []
    for name, spec in AGENT_REGISTRY.items():
        lines.append(f"- {name}: {spec.description}")
    return "\n".join(lines)


def registry_public() -> list[dict[str, Any]]:
    """Serializable agent list for the UI mission-control graph."""
    return [
        {"name": n, "description": s.description, "phase": s.phase}
        for n, s in AGENT_REGISTRY.items()
    ]
