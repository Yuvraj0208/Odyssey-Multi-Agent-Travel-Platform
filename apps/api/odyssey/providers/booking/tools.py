"""Booking operations exposed as LangChain tools.

Wrapping search/confirm/cancel as tools means the Booking agent's provider calls
surface natively in the mission-control activity feed, and the graph reads typed
results from the tool artifacts.
"""

from __future__ import annotations

from langchain_core.tools import tool

from odyssey.providers.booking.registry import ProviderError, get_provider_registry
from odyssey.schemas.booking import (
    ActivityQuery,
    FlightQuery,
    HotelQuery,
    PricedOffer,
    Traveler,
)
from odyssey.schemas.trip import Geo


@tool(response_format="content_and_artifact")
async def search_offers(
    category: str,
    destination: str,
    origin: str | None = None,
    depart_date: str | None = None,
    return_date: str | None = None,
    nights: int = 3,
    passengers: int = 1,
    interests: list[str] | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> tuple[str, dict]:
    """Search flight, hotel, or activity offers across providers and price the best one.

    category is one of "flight", "hotel", "activity". Returns up to 5 offers plus a
    priced top pick ready to stage for approval.
    """
    reg = get_provider_registry()
    geo = Geo(lat=lat, lng=lng) if (lat is not None and lng is not None) else None

    if category == "flight":
        if not origin:
            return ("No origin provided for flights.", {"offers": [], "priced_top": None})
        offers = await reg.search_flights(
            FlightQuery(origin=origin, destination=destination, depart_date=depart_date, return_date=return_date, passengers=passengers)
        )
    elif category == "hotel":
        offers = await reg.search_hotels(
            HotelQuery(destination=destination, geo=geo, checkin=depart_date, checkout=return_date, nights=nights, guests=passengers)
        )
    elif category == "activity":
        offers = await reg.search_activities(
            ActivityQuery(destination=destination, geo=geo, date=depart_date, interests=interests or [])
        )
    else:
        return (f"Unknown category {category!r}.", {"offers": [], "priced_top": None})

    if not offers:
        return (f"No {category} offers found.", {"offers": [], "priced_top": None})

    top = offers[0]
    prov = reg.provider_for(top.provider)
    priced = await prov.price(top.id)
    art = {"offers": [o.model_dump(mode="json") for o in offers[:5]], "priced_top": priced.model_dump(mode="json")}
    note = f"{len(offers)} {category} offers; best: {priced.title} ${priced.price:.0f}" + (
        " (price updated on re-quote)" if priced.price_changed else ""
    )
    return (note, art)


@tool(response_format="content_and_artifact")
async def confirm_offer(
    provider: str,
    offer_id: str,
    type: str,
    title: str,
    price: float,
    currency: str,
    idempotency_key: str,
) -> tuple[str, dict]:
    """Confirm (book) a priced offer with a provider. Idempotent on idempotency_key."""
    reg = get_provider_registry()
    prov = reg.provider_for(provider)
    if prov is None:
        return (f"Provider {provider} is unavailable.", {"error": "no_provider", "status": "failed"})
    priced = PricedOffer(offer_id=offer_id, type=type, provider=provider, title=title, price=price, currency=currency)
    try:
        conf = await prov.book(priced, Traveler(), idempotency_key)
        return (f"Confirmed {title} - ref {conf.booking_ref}", conf.model_dump(mode="json"))
    except ProviderError as e:
        return (f"Could not book {title}: {e}", {"error": str(e), "status": "failed", "title": title})


@tool(response_format="content_and_artifact")
async def cancel_offer(provider: str, booking_ref: str) -> tuple[str, dict]:
    """Cancel a confirmed booking by reference."""
    reg = get_provider_registry()
    prov = reg.provider_for(provider)
    if prov is None:
        return (f"Provider {provider} is unavailable.", {"error": "no_provider"})
    conf = await prov.cancel(booking_ref)
    return (f"Cancelled {booking_ref}", conf.model_dump(mode="json"))
