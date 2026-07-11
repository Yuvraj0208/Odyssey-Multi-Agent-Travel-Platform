"""Supervisor brief-merge + routing heuristic tests (no LLM)."""

from odyssey.agents.base import DESTINATION, PLANNER
from odyssey.agents.supervisor import DONE, BriefExtract, _heuristic_next, _merge_brief


def test_merge_brief_fills_and_nests():
    merged = _merge_brief(
        {"destination": "Kyoto"},
        BriefExtract(interests=["temples"], adults=2, budget_total=1500, currency="EUR", pace="relaxed"),
    )
    assert merged["destination"] == "Kyoto"
    assert merged["interests"] == ["temples"]
    assert merged["party"]["adults"] == 2
    assert merged["budget"]["total"] == 1500
    assert merged["budget"]["currency"] == "EUR"
    assert merged["pace"] == "relaxed"


def test_merge_brief_does_not_clobber_with_empty_lists():
    merged = _merge_brief({"interests": ["food"]}, BriefExtract(destination="Lisbon", interests=[]))
    assert merged["interests"] == ["food"]  # empty list from extract is ignored
    assert merged["destination"] == "Lisbon"


def test_heuristic_pipeline_progression():
    from odyssey.agents import bootstrap_agents
    from odyssey.agents.base import LOGISTICS, MEMORY

    bootstrap_agents()  # registers memory + logistics

    # no destination -> ask user (done)
    assert _heuristic_next({}, {}, None) == DONE
    dest = {"destination": "Kyoto"}
    # destination present, nothing loaded -> memory first (personalize before planning)
    assert _heuristic_next(dest, {}, None) == MEMORY
    # memory loaded, no research -> destination intelligence
    assert _heuristic_next(dest, {"memory_loaded": True}, None) == DESTINATION
    # research done, no itinerary -> planner
    assert _heuristic_next(dest, {"memory_loaded": True, "research_done": True}, None) == PLANNER
    # itinerary exists but not validated -> logistics
    ctx = {"memory_loaded": True, "research_done": True}
    assert _heuristic_next(dest, ctx, {"days": []}) == LOGISTICS
    # everything done -> done
    ctx2 = {"memory_loaded": True, "research_done": True, "logistics_done": True}
    assert _heuristic_next(dest, ctx2, {"days": []}) == DONE
