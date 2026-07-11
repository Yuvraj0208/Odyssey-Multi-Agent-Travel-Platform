"""Schema contract tests."""

from odyssey.schemas.trip import Geo, Itinerary, ItineraryDay, ItineraryItem, TripBrief


def test_itinerary_item_autogenerates_id():
    a = ItineraryItem(title="Kinkaku-ji")
    b = ItineraryItem(title="Fushimi Inari")
    assert a.id and b.id and a.id != b.id


def test_itinerary_cost_rollup():
    day = ItineraryDay(
        day=1,
        items=[
            ItineraryItem(title="A", cost_estimate=10),
            ItineraryItem(title="B", cost_estimate=5.5),
            ItineraryItem(title="Free sight", cost_estimate=0),
        ],
    )
    it = Itinerary(destination="Kyoto", days=[day])
    assert day.estimated_cost == 15.5
    assert it.estimated_total == 15.5


def test_trip_brief_defaults():
    b = TripBrief(destination="Lisbon")
    assert b.pace == "balanced"
    assert b.party.adults == 1
    assert b.budget.currency == "USD"


def test_itinerary_json_roundtrip():
    it = Itinerary(
        destination="Kyoto",
        center=Geo(lat=35.0, lng=135.7, name="Kyoto"),
        days=[ItineraryDay(day=1, items=[ItineraryItem(title="Temple", geo=Geo(lat=35.0, lng=135.8))])],
    )
    dumped = it.model_dump(mode="json")
    assert dumped["destination"] == "Kyoto"
    assert dumped["days"][0]["items"][0]["geo"]["lat"] == 35.0
    # rebuildable
    Itinerary.model_validate(dumped)
