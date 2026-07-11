"""Realistic mock providers.

Simulate real-world behavior so the degradation and human-in-the-loop paths are
genuinely exercised: network latency, occasional search failures, price changes on
re-quote, limited inventory (guarded by a lock), and idempotent booking (a repeated
idempotency_key never double-books).
"""

from __future__ import annotations

import asyncio
import hashlib
import random
import uuid

from odyssey.core.logging import get_logger
from odyssey.schemas.booking import (
    ActivityQuery,
    BookingConfirmation,
    BookingStatus,
    BookingType,
    FlightQuery,
    HotelQuery,
    Offer,
    PricedOffer,
    Traveler,
)
from odyssey.schemas.trip import Geo

log = get_logger(__name__)


class ProviderError(RuntimeError):
    """Recoverable provider failure; the agent degrades to other providers/offers."""


def _seed(*parts: str) -> random.Random:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


class _MockBase:
    """Shared mock behavior: latency, failures, pricing, inventory, idempotency."""

    def __init__(self, name: str, *, search_fail_rate: float = 0.0, book_fail_rate: float = 0.0):
        self.name = name
        self.search_fail_rate = search_fail_rate
        self.book_fail_rate = book_fail_rate
        self._offers: dict[str, Offer] = {}
        self._inventory: dict[str, int] = {}
        self._by_key: dict[str, BookingConfirmation] = {}
        self._by_ref: dict[str, BookingConfirmation] = {}
        self._lock = asyncio.Lock()

    async def _latency(self) -> None:
        await asyncio.sleep(random.uniform(0.05, 0.22))

    def _cache(self, offers: list[Offer], rng: random.Random) -> list[Offer]:
        for o in offers:
            self._offers[o.id] = o
            self._inventory.setdefault(o.id, rng.randint(2, 6))
        return offers

    async def price(self, offer_id: str) -> PricedOffer:
        await self._latency()
        offer = self._offers.get(offer_id)
        if not offer:
            raise ProviderError("offer no longer available")
        price, changed = offer.price, False
        if random.random() < 0.30:  # re-quote sometimes shifts price
            price = round(offer.price * (1 + random.uniform(-0.05, 0.10)), 2)
            changed = abs(price - offer.price) >= 0.01
        return PricedOffer(
            offer_id=offer.id,
            type=offer.type,
            provider=self.name,
            title=offer.title,
            price=price,
            currency=offer.currency,
            price_changed=changed,
            details=offer.details,
            cancellation=offer.cancellation,
        )

    async def book(
        self, priced: PricedOffer, traveler: Traveler, idempotency_key: str
    ) -> BookingConfirmation:
        await self._latency()
        async with self._lock:  # inventory + idempotency are guarded
            if idempotency_key in self._by_key:
                return self._by_key[idempotency_key]  # idempotent: never double-book
            if random.random() < self.book_fail_rate:
                raise ProviderError(f"{self.name}: booking system busy, try again")
            remaining = self._inventory.get(priced.offer_id, 5)
            if remaining <= 0:
                raise ProviderError(f"{priced.title} just sold out")
            self._inventory[priced.offer_id] = remaining - 1
            ref = f"{self.name[:2].upper()}-{uuid.uuid4().hex[:8].upper()}"
            conf = BookingConfirmation(
                booking_ref=ref,
                status=BookingStatus.confirmed,
                provider=self.name,
                type=priced.type,
                title=priced.title,
                price=priced.price,
                currency=priced.currency,
            )
            self._by_key[idempotency_key] = conf
            self._by_ref[ref] = conf
            log.info("provider.booked", provider=self.name, ref=ref, title=priced.title)
            return conf

    async def cancel(self, booking_ref: str) -> BookingConfirmation:
        await self._latency()
        existing = self._by_ref.get(booking_ref)
        conf = BookingConfirmation(
            booking_ref=booking_ref,
            status=BookingStatus.cancelled,
            provider=self.name,
            type=existing.type if existing else BookingType.activity,
            title=existing.title if existing else "Booking",
            price=existing.price if existing else 0.0,
            currency=existing.currency if existing else "USD",
        )
        if existing:
            existing.status = BookingStatus.cancelled
        log.info("provider.cancelled", provider=self.name, ref=booking_ref)
        return conf


_AIRLINES = [("SkyJet", "SJ"), ("AeroNova", "AN"), ("Meridian Air", "MA"), ("Polaris", "PL")]
_HOTEL_ADJ = ["Grand", "Boutique", "Riverside", "Central", "Garden", "Old Town"]
_HOTEL_KIND = ["Hotel", "Suites", "Residences", "Inn"]


class MockFlightProvider(_MockBase):
    async def search(self, q: FlightQuery) -> list[Offer]:
        await self._latency()
        if random.random() < self.search_fail_rate:
            raise ProviderError(f"{self.name}: flight search timed out")
        rng = _seed(self.name, q.origin, q.destination, q.depart_date or "")
        base = 120 + (hash((q.origin, q.destination)) % 400)
        offers = []
        for airline, code in rng.sample(_AIRLINES, k=rng.randint(2, 3)):
            stops = rng.choice([0, 0, 1])
            dur = rng.randint(90, 240) + stops * rng.randint(60, 120)
            dep_h = rng.randint(6, 20)
            price = round(base * rng.uniform(0.8, 1.6) + stops * 30 + q.passengers * 0, 2)
            offers.append(
                Offer(
                    type=BookingType.flight,
                    provider=self.name,
                    title=f"{airline} {code}{rng.randint(100, 999)} {q.origin}->{q.destination}",
                    price=round(price * q.passengers, 2),
                    currency="USD",
                    cancellation="Non-refundable" if rng.random() < 0.4 else "Free cancellation up to 24h",
                    details={
                        "airline": airline,
                        "stops": stops,
                        "duration_min": dur,
                        "depart": f"{dep_h:02d}:{rng.choice(['00','15','30','45'])}",
                        "cabin": q.cabin,
                        "passengers": q.passengers,
                        "route": f"{q.origin} -> {q.destination}",
                    },
                )
            )
        return self._cache(sorted(offers, key=lambda o: o.price), rng)


class MockHotelProvider(_MockBase):
    async def search(self, q: HotelQuery) -> list[Offer]:
        await self._latency()
        if random.random() < self.search_fail_rate:
            raise ProviderError(f"{self.name}: hotel search timed out")
        rng = _seed(self.name, q.destination, q.checkin or "")
        nights = max(1, q.nights)
        offers = []
        for _ in range(rng.randint(2, 3)):
            adj = rng.choice(_HOTEL_ADJ)
            kind = rng.choice(_HOTEL_KIND)
            rating = rng.choice([3.5, 4.0, 4.2, 4.5, 4.7, 4.8])
            per_night = round(60 + rating * rng.uniform(15, 45), 2)
            geo = None
            if q.geo:
                geo = Geo(lat=q.geo.lat + rng.uniform(-0.02, 0.02), lng=q.geo.lng + rng.uniform(-0.02, 0.02), name=f"{adj} {q.destination} {kind}")
            offers.append(
                Offer(
                    type=BookingType.hotel,
                    provider=self.name,
                    title=f"{adj} {q.destination} {kind}",
                    price=round(per_night * nights, 2),
                    currency="USD",
                    geo=geo,
                    cancellation="Free cancellation up to 48h" if rng.random() < 0.7 else "Non-refundable",
                    details={
                        "rating": rating,
                        "price_per_night": per_night,
                        "nights": nights,
                        "board": rng.choice(["Room only", "Breakfast included"]),
                        "checkin": q.checkin,
                        "checkout": q.checkout,
                        "guests": q.guests,
                    },
                )
            )
        return self._cache(sorted(offers, key=lambda o: o.price), rng)


class MockActivityProvider(_MockBase):
    async def search(self, q: ActivityQuery) -> list[Offer]:
        await self._latency()
        if random.random() < self.search_fail_rate:
            raise ProviderError(f"{self.name}: activity search timed out")
        rng = _seed(self.name, q.destination, ",".join(q.interests))
        ideas = [
            f"Guided food tour of {q.destination}",
            f"{q.destination} highlights walking tour",
            f"Skip-the-line museum pass ({q.destination})",
            f"Sunset viewpoint experience in {q.destination}",
            f"Local cooking class in {q.destination}",
        ]
        offers = []
        for title in rng.sample(ideas, k=rng.randint(2, 3)):
            offers.append(
                Offer(
                    type=BookingType.activity,
                    provider=self.name,
                    title=title,
                    price=round(rng.uniform(25, 95), 2),
                    currency="USD",
                    geo=q.geo,
                    cancellation="Free cancellation up to 24h",
                    details={"date": q.date, "duration_min": rng.choice([90, 120, 150, 180])},
                )
            )
        return self._cache(sorted(offers, key=lambda o: o.price), rng)
