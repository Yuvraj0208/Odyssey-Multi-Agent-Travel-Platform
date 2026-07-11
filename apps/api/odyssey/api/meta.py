"""Metadata endpoints for the UI (agent roster for mission-control, etc.)."""

from __future__ import annotations

from fastapi import APIRouter

from odyssey.agents import bootstrap_agents
from odyssey.agents.base import SUPERVISOR
from odyssey.graph.registry import registry_public

router = APIRouter(tags=["meta"])


@router.get("/agents")
async def agents() -> dict:
    bootstrap_agents()
    roster = [
        {"name": SUPERVISOR, "description": "Orchestrates the team and routes work.", "phase": 1, "role": "supervisor"},
    ]
    for a in registry_public():
        roster.append({**a, "role": "specialist"})
    return {"agents": roster}
