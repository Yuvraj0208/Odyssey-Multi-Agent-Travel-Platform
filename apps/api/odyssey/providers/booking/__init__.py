"""Booking providers behind swappable Protocol interfaces.

Real-time flights/hotels/activities have no fully open source, so Odyssey ships
realistic mock providers that simulate latency, occasional failures, re-quote price
changes, limited inventory, and idempotent booking. A real provider (e.g. Amadeus
Self-Service) can slot in behind the same Protocols with no agent changes.
"""

from odyssey.providers.booking.registry import (
    ProviderError,
    get_provider_registry,
)

__all__ = ["ProviderError", "get_provider_registry"]
