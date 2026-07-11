"""Provider registry: query several providers at once and merge results.

One secondary provider per category has a nonzero failure rate so the merge + graceful
degradation path is genuinely exercised (a failing provider never blocks results).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from odyssey.core.logging import get_logger
from odyssey.providers.booking.mock import (
    MockActivityProvider,
    MockFlightProvider,
    MockHotelProvider,
    ProviderError,
)
from odyssey.schemas.booking import ActivityQuery, FlightQuery, HotelQuery, Offer

log = get_logger(__name__)

__all__ = ["ProviderError", "ProviderRegistry", "get_provider_registry"]


@dataclass
class ProviderRegistry:
    flights: list
    hotels: list
    activities: list

    def all_providers(self) -> list:
        return [*self.flights, *self.hotels, *self.activities]

    def provider_for(self, name: str):
        for p in self.all_providers():
            if p.name == name:
                return p
        return None

    async def _search_all(self, providers: list, q, kind: str) -> list[Offer]:
        results = await asyncio.gather(
            *(p.search(q) for p in providers), return_exceptions=True
        )
        offers: list[Offer] = []
        for p, r in zip(providers, results, strict=False):
            if isinstance(r, Exception):
                log.warning("provider.search_failed", kind=kind, provider=p.name, error=str(r))
                continue
            offers.extend(r)
        return sorted(offers, key=lambda o: o.price)

    async def search_flights(self, q: FlightQuery) -> list[Offer]:
        return await self._search_all(self.flights, q, "flight")

    async def search_hotels(self, q: HotelQuery) -> list[Offer]:
        return await self._search_all(self.hotels, q, "hotel")

    async def search_activities(self, q: ActivityQuery) -> list[Offer]:
        return await self._search_all(self.activities, q, "activity")


_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry(
            flights=[
                MockFlightProvider("SkyLink"),
                MockFlightProvider("Voyair", search_fail_rate=0.15),
            ],
            hotels=[
                MockHotelProvider("StayHub"),
                MockHotelProvider("RoomFinder", search_fail_rate=0.15),
            ],
            activities=[MockActivityProvider("TourDesk")],
        )
    return _registry
