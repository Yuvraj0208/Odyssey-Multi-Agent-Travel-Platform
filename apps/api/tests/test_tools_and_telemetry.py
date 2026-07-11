"""POI selector mapping, telemetry accounting, and stream helpers (no network/LLM)."""

from odyssey.core.telemetry import SessionTelemetry
from odyssey.graph.stream import _agent_from_tags, _extract_usage
from odyssey.providers.tools.poi import _category_for, _selectors_for


def test_poi_selectors_include_base_and_interests():
    sels = _selectors_for(["temples", "food"])
    flat = [s for s, _ in sels]
    assert any("tourism" in s and "attraction" in s for s in flat)  # base always present
    assert any("place_of_worship" in s for s in flat)  # temples
    assert any("restaurant" in s for s in flat)  # food


def test_poi_category_mapping():
    assert _category_for("place_of_worship") == "spiritual"
    assert _category_for("restaurant") == "food"
    assert _category_for("unknown_kind") == "attraction"


def test_telemetry_cost_and_snapshot():
    tel = SessionTelemetry(session_id="s1")
    tel.add_usage(1000, 500, "llama-3.3-70b-versatile")
    snap = tel.snapshot()
    assert snap["total_tokens"] == 1500
    assert snap["estimated_cost_usd"] > 0
    assert snap["model"] == "llama-3.3-70b-versatile"


def test_agent_from_tags():
    assert _agent_from_tags(["agent:trip_planner", "seq:1"], "fallback") == "trip_planner"
    assert _agent_from_tags(["seq:1"], "fallback") == "fallback"


def test_extract_usage_from_message_like():
    class Msg:
        usage_metadata = {"input_tokens": 12, "output_tokens": 7}
        response_metadata = {"model_name": "llama-3.3-70b-versatile"}

    itok, otok, model = _extract_usage(Msg())
    assert (itok, otok) == (12, 7)
    assert model == "llama-3.3-70b-versatile"
