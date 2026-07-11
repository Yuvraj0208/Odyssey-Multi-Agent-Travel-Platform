"""Provider Protocols. Agents depend on these, never on concrete providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from odyssey.schemas.booking import (
    ActivityQuery,
    BookingConfirmation,
    FlightQuery,
    HotelQuery,
    Offer,
    PricedOffer,
    Traveler,
)


@runtime_checkable
class FlightProvider(Protocol):
    name: str

    async def search(self, q: FlightQuery) -> list[Offer]: ...
    async def price(self, offer_id: str) -> PricedOffer: ...
    async def book(
        self, priced: PricedOffer, traveler: Traveler, idempotency_key: str
    ) -> BookingConfirmation: ...
    async def cancel(self, booking_ref: str) -> BookingConfirmation: ...


@runtime_checkable
class HotelProvider(Protocol):
    name: str

    async def search(self, q: HotelQuery) -> list[Offer]: ...
    async def price(self, offer_id: str) -> PricedOffer: ...
    async def book(
        self, priced: PricedOffer, traveler: Traveler, idempotency_key: str
    ) -> BookingConfirmation: ...
    async def cancel(self, booking_ref: str) -> BookingConfirmation: ...


@runtime_checkable
class ActivityProvider(Protocol):
    name: str

    async def search(self, q: ActivityQuery) -> list[Offer]: ...
    async def price(self, offer_id: str) -> PricedOffer: ...
    async def book(
        self, priced: PricedOffer, traveler: Traveler, idempotency_key: str
    ) -> BookingConfirmation: ...
    async def cancel(self, booking_ref: str) -> BookingConfirmation: ...
