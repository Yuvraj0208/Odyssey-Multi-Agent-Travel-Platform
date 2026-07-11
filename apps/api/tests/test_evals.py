"""Eval deterministic checks (no LLM)."""

from odyssey.evals.checks import (
    budget_respected,
    grounded_in_real_pois,
    no_double_booking,
    run_deterministic_checks,
    timing_feasible,
)

ITIN = {
    "days": [
        {"day": 1, "travel_min": 40, "items": [
            {"title": "Kinkaku-ji", "geo": {"lat": 35, "lng": 135}, "cost_estimate": 5},
            {"title": "Nishiki Market", "geo": {"lat": 35, "lng": 135}, "cost_estimate": 20},
        ]},
    ]
}
POIS = [{"name": "Kinkaku-ji"}, {"name": "Nishiki Market"}]


def test_budget_respected():
    assert budget_respected(ITIN, {"budget": {"total": 100}}).passed
    assert not budget_respected(ITIN, {"budget": {"total": 10}}).passed
    assert budget_respected(ITIN, {}).passed  # no budget -> pass


def test_timing_feasible():
    assert timing_feasible(ITIN).passed
    assert not timing_feasible({"days": [{"day": 1, "travel_min": 300, "items": []}]}).passed


def test_no_double_booking():
    assert no_double_booking([{"type": "hotel", "title": "H", "booking_ref": "A1"}]).passed
    dupe = [{"type": "hotel", "title": "H", "booking_ref": "A1"}, {"type": "hotel", "title": "H", "booking_ref": "A2"}]
    assert not no_double_booking(dupe).passed
    # cancelled ones are ignored
    ok = [{"type": "hotel", "title": "H", "booking_ref": "A1"}, {"type": "hotel", "title": "H", "status": "cancelled"}]
    assert no_double_booking(ok).passed


def test_grounded_in_real_pois():
    assert grounded_in_real_pois(ITIN, POIS).passed
    assert not grounded_in_real_pois(ITIN, [{"name": "Somewhere Else"}]).passed


def test_run_deterministic_checks_aggregate():
    results = run_deterministic_checks({"itinerary": ITIN, "trip_brief": {"budget": {"total": 100}}, "confirmed_bookings": []}, POIS)
    assert len(results) == 4
    assert all(c.passed for c in results)
