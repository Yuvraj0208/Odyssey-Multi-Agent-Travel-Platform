"""Booking domain: queries, offers, and bookings.

These are the contracts shared by the provider Protocols, the Booking agent, and
the UI. A Booking moves offered -> pending_approval -> confirmed | cancelled, always
carrying an idempotency_key so a retried confirm never double-books.
"""

from __future__ import annotations

import time
import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

from odyssey.schemas.trip import Geo


class BookingType(StrEnum):
    flight = "flight"
    hotel = "hotel"
    activity = "activity"


class BookingStatus(StrEnum):
    offered = "offered"
    pending_approval = "pending_approval"
    confirmed = "confirmed"
    cancelled = "cancelled"
    failed = "failed"


# ---- Queries ----


class FlightQuery(BaseModel):
    origin: str
    destination: str
    depart_date: str | None = None
    return_date: str | None = None
    passengers: int = 1
    cabin: str = "economy"


class HotelQuery(BaseModel):
    destination: str
    geo: Geo | None = None
    checkin: str | None = None
    checkout: str | None = None
    nights: int = 3
    guests: int = 1
    rooms: int = 1


class ActivityQuery(BaseModel):
    destination: str
    geo: Geo | None = None
    date: str | None = None
    interests: list[str] = Field(default_factory=list)


# ---- Offers ----


class Offer(BaseModel):
    id: str = Field(default_factory=lambda: "of_" + uuid.uuid4().hex[:10])
    type: BookingType
    provider: str
    title: str
    price: float
    currency: str = "USD"
    details: dict = Field(default_factory=dict)
    geo: Geo | None = None
    cancellation: str = "Free cancellation up to 24h before"


class PricedOffer(BaseModel):
    offer_id: str
    type: BookingType
    provider: str
    title: str
    price: float  # may differ from the search price (re-quote)
    currency: str = "USD"
    price_changed: bool = False
    expires_at: float = Field(default_factory=lambda: time.time() + 600)
    details: dict = Field(default_factory=dict)
    cancellation: str = "Free cancellation up to 24h before"


class Traveler(BaseModel):
    # Mock bookings only - no real PII or payment is ever collected.
    name: str = "Guest Traveler"
    email: str | None = None


class BookingConfirmation(BaseModel):
    booking_ref: str
    status: BookingStatus
    provider: str
    type: BookingType
    title: str
    price: float
    currency: str = "USD"
    confirmed_at: float = Field(default_factory=lambda: time.time())


class Booking(BaseModel):
    """A staged or confirmed booking carried in TravelState."""

    id: str = Field(default_factory=lambda: "bk_" + uuid.uuid4().hex[:10])
    type: BookingType
    action: str = "book"  # book | cancel
    provider: str
    title: str
    price: float
    currency: str = "USD"
    status: BookingStatus = BookingStatus.pending_approval
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex)
    offer_id: str | None = None
    booking_ref: str | None = None
    cancellation: str = "Free cancellation up to 24h before"
    details: dict = Field(default_factory=dict)
    created_at: float = Field(default_factory=lambda: time.time())
