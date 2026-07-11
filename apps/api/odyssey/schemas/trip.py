"""Trip domain schemas: the API contracts for briefs, itineraries, and options.

These are the typed shapes agents read and write inside TravelState. Kept in sync
with the SQLAlchemy persistence models in odyssey/db.
"""

from __future__ import annotations

import datetime as _dt
import uuid
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


def _item_id() -> str:
    return uuid.uuid4().hex[:10]


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.UTC)


class Geo(BaseModel):
    lat: float
    lng: float
    name: str | None = None


class Party(BaseModel):
    adults: int = 1
    children: int = 0
    infants: int = 0


class Budget(BaseModel):
    total: float | None = None
    currency: str = "USD"
    per_category: dict[str, float] = Field(default_factory=dict)


class TripBrief(BaseModel):
    """Normalized trip request extracted from the conversation."""

    destination: str | None = None
    origin: str | None = None
    geo: Geo | None = None
    start_date: _dt.date | None = None
    end_date: _dt.date | None = None
    duration_days: int | None = None
    party: Party = Field(default_factory=Party)
    budget: Budget = Field(default_factory=Budget)
    pace: Literal["relaxed", "balanced", "packed"] = "balanced"
    interests: list[str] = Field(default_factory=list)
    must_haves: list[str] = Field(default_factory=list)
    must_avoids: list[str] = Field(default_factory=list)
    style: str | None = None
    notes: str | None = None


class ItemType(StrEnum):
    attraction = "attraction"
    food = "food"
    activity = "activity"
    transport = "transport"
    lodging = "lodging"
    flight = "flight"
    free = "free"


class ItineraryItem(BaseModel):
    id: str = Field(default_factory=_item_id)
    type: ItemType = ItemType.attraction
    title: str
    description: str | None = None
    geo: Geo | None = None
    start: str | None = None  # "09:00"
    end: str | None = None  # "11:00"
    duration_min: int | None = None
    cost_estimate: float | None = None
    currency: str = "USD"
    source: str | None = None  # which tool/agent produced it
    booking_ref: str | None = None
    weather_note: str | None = None
    tags: list[str] = Field(default_factory=list)
    # Logistics annotations: travel to the next stop in the day.
    transit_to_next_min: float | None = None
    transit_to_next_km: float | None = None
    transit_mode: str | None = None


class ItineraryDay(BaseModel):
    day: int
    date: _dt.date | None = None
    summary: str | None = None
    items: list[ItineraryItem] = Field(default_factory=list)
    travel_min: float | None = None  # total intra-day travel (logistics)
    feasible: bool | None = None

    @property
    def estimated_cost(self) -> float:
        return sum((i.cost_estimate or 0.0) for i in self.items)


class Itinerary(BaseModel):
    destination: str | None = None
    center: Geo | None = None
    days: list[ItineraryDay] = Field(default_factory=list)
    currency: str = "USD"
    summary: str | None = None
    updated_at: _dt.datetime = Field(default_factory=_now)

    @property
    def estimated_total(self) -> float:
        return sum(d.estimated_cost for d in self.days)
