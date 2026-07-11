"""Agent package.

Importing this package registers every agent in AGENT_REGISTRY via import side
effects. bootstrap_agents() is idempotent and safe to call at graph-build time.
"""

from __future__ import annotations

_BOOTSTRAPPED = False


def bootstrap_agents() -> None:
    """Import agent modules so they self-register. Idempotent."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    # Import for registration side effects. Order is irrelevant (loose coupling).
    from odyssey.agents import (  # noqa: F401
        booking,
        destination,
        logistics,
        memory,
        planner,
        support,
    )

    _BOOTSTRAPPED = True
