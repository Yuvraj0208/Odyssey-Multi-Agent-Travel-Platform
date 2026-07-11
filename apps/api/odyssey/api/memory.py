"""Long-term memory management for the preferences screen."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from odyssey.api.deps import CurrentUser, current_user
from odyssey.graph.runtime import get_runtime

router = APIRouter(tags=["memory"])


class MemoryIn(BaseModel):
    text: str = Field(min_length=2, max_length=200)
    kind: str = "preference"
    tags: list[str] = Field(default_factory=list)


@router.get("/memory")
async def list_memory(user: CurrentUser = Depends(current_user)) -> dict:
    from odyssey.memory.store_repo import all_memories

    runtime = await get_runtime()
    return {"memories": await all_memories(runtime.store, user.id)}


@router.post("/memory")
async def add_memory(body: MemoryIn, user: CurrentUser = Depends(current_user)) -> dict:
    from odyssey.memory.store_repo import MemoryFact, remember

    runtime = await get_runtime()
    await remember(runtime.store, user.id, MemoryFact(text=body.text, kind=body.kind, tags=body.tags))
    return {"ok": True}


@router.delete("/memory/{key}")
async def delete_memory_endpoint(key: str, user: CurrentUser = Depends(current_user)) -> dict:
    from odyssey.memory.store_repo import delete_memory

    runtime = await get_runtime()
    await delete_memory(runtime.store, user.id, key)
    return {"ok": True}
