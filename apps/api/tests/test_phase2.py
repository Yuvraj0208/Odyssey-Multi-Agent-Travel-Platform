"""Phase 2: memory ranking, conditions monitor, routing fallback (no network/LLM)."""

import pytest

from odyssey.memory.store_repo import _score
from odyssey.proactive.monitor import _adverse, _is_outdoor
from odyssey.providers.tools.routing import _fallback, _haversine_km


def test_memory_score_overlap():
    mem = {"text": "Loves temples and gardens", "tags": ["temples", "gardens"]}
    # counts distinct query terms present: "temples" hits, "food" does not
    assert _score(mem, {"temples", "food"}) == 1
    assert _score(mem, {"temples", "gardens"}) == 2
    assert _score(mem, {"nightlife"}) == 0


def test_monitor_adverse_detection():
    assert _adverse({"condition": "heavy rain", "precip_prob_pct": 80}) is True
    assert _adverse({"condition": "clear", "precip_prob_pct": 70}) is True  # high precip prob
    assert _adverse({"condition": "clear", "precip_prob_pct": 10}) is False


def test_monitor_outdoor_classification():
    assert _is_outdoor({"type": "attraction"}) is True
    assert _is_outdoor({"type": "food"}) is False
    # already flagged/handled items are not re-flagged
    assert _is_outdoor({"type": "attraction", "weather_note": "moved indoors"}) is False


def test_haversine_reasonable():
    # Park Guell -> Sagrada Familia, ~2.6 km straight line
    km = _haversine_km((41.4145, 2.1527), (41.4036, 2.1744))
    assert 1.5 < km < 3.5


def test_routing_fallback_shape():
    coords = [[2.1527, 41.4145], [2.1744, 41.4036]]  # [lng, lat]
    art = _fallback(coords, "walking")
    assert art["source"] == "estimate"
    assert len(art["legs"]) == 1
    assert art["total_min"] > 0 and art["total_km"] > 0


@pytest.mark.asyncio
async def test_memory_roundtrip_inmemory_store():
    from langgraph.store.memory import InMemoryStore

    from odyssey.memory.store_repo import MemoryFact, all_memories, recall, remember

    store = InMemoryStore()
    await remember(store, "u1", MemoryFact(text="Loves temples", tags=["temples"]))
    await remember(store, "u1", MemoryFact(text="Vegetarian", kind="constraint", tags=["food", "vegetarian"]))
    mems = await all_memories(store, "u1")
    assert len(mems) == 2
    ranked = await recall(store, "u1", ["temples"], limit=5)
    assert ranked[0]["text"] == "Loves temples"  # best overlap ranked first
