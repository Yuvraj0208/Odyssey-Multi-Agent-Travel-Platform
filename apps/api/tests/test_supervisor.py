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


def test_heuristic_routing_progression():
    # no destination -> ask user (done)
    assert _heuristic_next({}, {}, None) == DONE
    # destination, no research -> destination intelligence
    assert _heuristic_next({"destination": "Kyoto"}, {}, None) == DESTINATION
    # research done, no itinerary -> planner
    assert _heuristic_next({"destination": "Kyoto"}, {"research_done": True}, None) == PLANNER
    # itinerary exists -> done
    assert _heuristic_next({"destination": "Kyoto"}, {"research_done": True}, {"days": []}) == DONE
