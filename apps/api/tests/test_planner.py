"""Trip planner mapping + fallback tests (no LLM)."""

from odyssey.agents.planner import PlanItem, PlanOutput, _fallback_itinerary, _num_days, _to_itinerary

BRIEF = {"destination": "Kyoto", "duration_days": 2, "pace": "balanced", "budget": {"currency": "USD"}}
CTX = {
    "destination": {"name": "Kyoto", "lat": 35.0, "lng": 135.76},
    "pois": [
        {"name": "Kinkaku-ji", "lat": 35.039, "lng": 135.729, "category": "spiritual"},
        {"name": "Nishiki Market", "lat": 35.005, "lng": 135.764, "category": "food"},
        {"name": "Fushimi Inari", "lat": 34.967, "lng": 135.772, "category": "spiritual"},
    ],
    "weather": {"days": [], "rainy_days": []},
}


def test_num_days_from_duration_and_dates():
    assert _num_days({"duration_days": 4}) == 4
    assert _num_days({"start_date": "2026-04-01", "end_date": "2026-04-03"}) == 3
    assert _num_days({}) == 3  # default


def test_to_itinerary_attaches_real_geo_from_pois():
    plan = PlanOutput(
        summary="Two days in Kyoto",
        items=[
            PlanItem(day=1, title="Golden Pavilion", poi_name="Kinkaku-ji", start="09:00", type="attraction"),
            PlanItem(day=1, title="Lunch", poi_name="Nishiki Market", start="12:30", type="food", cost_estimate=20),
            PlanItem(day=2, title="Shrine gates", poi_name="Fushimi Inari", start="09:00"),
            PlanItem(day=2, title="Made up place", poi_name="Nonexistent", start="14:00"),
        ],
    )
    it = _to_itinerary(BRIEF, CTX, plan)
    assert len(it.days) == 2
    d1 = it.days[0]
    # geo attached from the real POI list, not hallucinated
    assert d1.items[0].geo is not None
    assert abs(d1.items[0].geo.lat - 35.039) < 1e-6
    # unknown poi_name -> no geo, but item still kept
    d2 = it.days[1]
    assert any(i.title == "Made up place" and i.geo is None for i in d2.items)
    # center from destination
    assert it.center and abs(it.center.lat - 35.0) < 1e-6


def test_fallback_spreads_pois_across_days():
    it = _fallback_itinerary(BRIEF, CTX)
    assert len(it.days) == 2
    placed = [i for d in it.days for i in d.items]
    assert len(placed) >= 1
    assert all(i.geo is not None for i in placed)  # every fallback item has real coords
