"""Long-term semantic memory over the LangGraph store, namespaced per user.

Memories are small durable facts about a traveler (preferences, dislikes,
constraints, style, past destinations). Retrieval ranks by term overlap against
the current trip so the most relevant facts are injected into planning.

The store backend is mode-aware (InMemoryStore local / AsyncPostgresStore stack).
For true vector recall, the same repository can be pointed at Qdrant / an embedding
index without changing callers - the ranking function is the only swap point.
"""

from __future__ import annotations

import time
import uuid

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

from odyssey.agents.base import safe_structured
from odyssey.core.logging import get_logger
from odyssey.providers.llm_provider import get_chat_model

log = get_logger(__name__)

_KINDS = ("preference", "dislike", "constraint", "style", "past_trip")


def _ns(user_id: str) -> tuple[str, str]:
    return ("memories", user_id)


class MemoryFact(BaseModel):
    text: str = Field(description="a concise, durable fact about the traveler")
    kind: str = Field(default="preference", description="|".join(_KINDS))
    tags: list[str] = Field(default_factory=list, description="lowercase keywords, e.g. temples, food")


class MemoryExtraction(BaseModel):
    facts: list[MemoryFact] = Field(default_factory=list)


async def remember(store, user_id: str, fact: MemoryFact) -> None:
    await store.aput(
        _ns(user_id),
        uuid.uuid4().hex[:12],
        {"text": fact.text, "kind": fact.kind, "tags": [t.lower() for t in fact.tags], "ts": time.time()},
    )


async def all_memories(store, user_id: str) -> list[dict]:
    items = await store.asearch(_ns(user_id), limit=200)
    out = []
    for it in items:
        v = it.value
        out.append({"key": it.key, **v})
    return out


def _score(mem: dict, terms: set[str]) -> int:
    hay = " ".join([mem.get("text", ""), " ".join(mem.get("tags", []))]).lower()
    return sum(1 for t in terms if t and t in hay)


async def recall(store, user_id: str, terms: list[str], limit: int = 8) -> list[dict]:
    """Return the most relevant memories for the given query terms (recency-tiebroken)."""
    mems = await all_memories(store, user_id)
    if not mems:
        return []
    tset = {t.lower().strip() for t in terms if t}
    ranked = sorted(mems, key=lambda m: (_score(m, tset), m.get("ts", 0)), reverse=True)
    # Keep those with any overlap; if none overlap, still surface a few recent ones.
    hit = [m for m in ranked if _score(m, tset) > 0]
    return (hit or ranked)[:limit]


async def extract_and_store(
    store, user_id: str, messages: list[BaseMessage], brief: dict | None
) -> list[str]:
    """Extract durable traveler facts from the turn and persist new, non-duplicate ones."""
    from langchain_core.messages import SystemMessage

    existing = await all_memories(store, user_id)
    existing_texts = {m.get("text", "").strip().lower() for m in existing}

    prompt = (
        "Extract durable, reusable facts about THIS traveler from the conversation - things worth "
        "remembering for future trips: preferences, dislikes, constraints (budget level, pace, "
        "accessibility, dietary), travel style, and destinations they have planned or visited. "
        "Do NOT include one-off trip details (specific dates, this trip's itinerary). Keep each fact "
        "short and general. Return an empty list if nothing durable is present."
    )
    brief_hint = f"\nTrip brief so far: {brief}" if brief else ""
    result = await safe_structured(
        get_chat_model(),
        MemoryExtraction,
        [SystemMessage(content=prompt + brief_hint), *messages],
        agent="memory",
    )
    if not result:
        return []

    stored: list[str] = []
    for fact in result.facts:
        text = fact.text.strip()
        if not text or text.lower() in existing_texts:
            continue
        if fact.kind not in _KINDS:
            fact.kind = "preference"
        await remember(store, user_id, fact)
        existing_texts.add(text.lower())
        stored.append(text)
    if stored:
        log.info("memory.stored", user_id=user_id, count=len(stored))
    return stored
