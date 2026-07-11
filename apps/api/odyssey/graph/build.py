"""Graph assembly.

  START -> supervisor -> (conditional) -> specialist -> supervisor -> ... -> END

Specialists are discovered from AGENT_REGISTRY, so adding an agent needs no edit
here. interrupt_before wires the human-in-the-loop gate for booking confirmation
(active once the booking agent registers a `booking_confirm` node in Phase 3).
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from odyssey.agents import bootstrap_agents
from odyssey.agents.base import SUPERVISOR
from odyssey.agents.supervisor import DONE, route_from_supervisor, supervisor_node
from odyssey.core.logging import get_logger
from odyssey.graph.registry import AGENT_REGISTRY
from odyssey.graph.state import TravelState

log = get_logger(__name__)


def build_graph(checkpointer: Any, store: Any):
    bootstrap_agents()

    b = StateGraph(TravelState)
    b.add_node(SUPERVISOR, supervisor_node)
    for name, spec in AGENT_REGISTRY.items():
        b.add_node(name, spec.build())

    b.add_edge(START, SUPERVISOR)
    b.add_conditional_edges(
        SUPERVISOR,
        route_from_supervisor,
        {**{n: n for n in AGENT_REGISTRY}, DONE: END},
    )
    for name in AGENT_REGISTRY:
        b.add_edge(name, SUPERVISOR)

    # Human-in-the-loop gate: pause before confirming a booking, if that node exists.
    interrupt_before = ["booking_confirm"] if "booking_confirm" in AGENT_REGISTRY else []

    graph = b.compile(
        checkpointer=checkpointer,
        store=store,
        interrupt_before=interrupt_before,
    )
    log.info("graph.built", agents=list(AGENT_REGISTRY.keys()), interrupts=interrupt_before)
    return graph
