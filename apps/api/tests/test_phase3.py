"""Phase 3: providers (idempotency, inventory, degradation) + booking staging (no LLM)."""

import pytest

from odyssey.agents.booking import _booking_from_priced
from odyssey.providers.booking.mock import MockFlightProvider, ProviderError
from odyssey.providers.booking.registry import ProviderRegistry
from odyssey.schemas.booking import (
    BookingStatus,
    BookingType,
    FlightQuery,
    Traveler,
)


@pytest.mark.asyncio
async def test_booking_is_idempotent():
    prov = MockFlightProvider("Test")
    offers = await prov.search(FlightQuery(origin="LIS", destination="BCN"))
    priced = await prov.price(offers[0].id)
    c1 = await prov.book(priced, Traveler(), "key-abc")
    c2 = await prov.book(priced, Traveler(), "key-abc")  # same key
    assert c1.booking_ref == c2.booking_ref  # never double-books


@pytest.mark.asyncio
async def test_inventory_sells_out():
    prov = MockFlightProvider("Test")
    offers = await prov.search(FlightQuery(origin="LIS", destination="BCN"))
    priced = await prov.price(offers[0].id)
    prov._inventory[priced.offer_id] = 1  # force scarce inventory
    await prov.book(priced, Traveler(), "k1")
    with pytest.raises(ProviderError):
        await prov.book(priced, Traveler(), "k2")  # different key, no stock


@pytest.mark.asyncio
async def test_registry_degrades_on_provider_failure():
    good = MockFlightProvider("Good")
    bad = MockFlightProvider("Bad", search_fail_rate=1.0)  # always fails
    reg = ProviderRegistry(flights=[good, bad], hotels=[], activities=[])
    offers = await reg.search_flights(FlightQuery(origin="LIS", destination="BCN"))
    assert offers  # good provider's offers still returned despite bad's failure
    assert all(o.provider == "Good" for o in offers)


def test_booking_from_priced():
    priced = {
        "offer_id": "of_1",
        "type": "hotel",
        "provider": "StayHub",
        "title": "Grand Hotel",
        "price": 420.0,
        "currency": "USD",
        "cancellation": "Free cancellation",
    }
    b = _booking_from_priced(priced)
    assert b.type == BookingType.hotel
    assert b.status == BookingStatus.pending_approval
    assert b.idempotency_key  # generated
    assert b.price == 420.0


@pytest.mark.asyncio
async def test_cancel_marks_cancelled():
    prov = MockFlightProvider("Test")
    offers = await prov.search(FlightQuery(origin="LIS", destination="BCN"))
    priced = await prov.price(offers[0].id)
    conf = await prov.book(priced, Traveler(), "k1")
    cancelled = await prov.cancel(conf.booking_ref)
    assert cancelled.status == BookingStatus.cancelled
