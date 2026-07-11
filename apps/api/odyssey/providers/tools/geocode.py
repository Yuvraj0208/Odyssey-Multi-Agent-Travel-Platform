"""Geocoding (no key).

Primary: Open-Meteo geocoding API - reliable, keyless, no UA policy, same provider
as the weather tool. Fallback: OSM Nominatim for specific landmarks Open-Meteo may
not resolve. Either way the tool degrades gracefully to an error artifact.
"""

from __future__ import annotations

from langchain_core.tools import tool

from odyssey.core.config import get_settings
from odyssey.providers.http import ToolError, http_client

_OPEN_METEO_GEO = "https://geocoding-api.open-meteo.com/v1/search"
_NOMINATIM = "https://nominatim.openstreetmap.org/search"


async def _open_meteo(query: str) -> dict | None:
    # Open-Meteo matches on a place name; drop a trailing ", Country" and use it as a hint.
    parts = [p.strip() for p in query.split(",") if p.strip()]
    name = parts[0] if parts else query
    hint = parts[-1].lower() if len(parts) > 1 else None
    try:
        data = await http_client.get_json(
            _OPEN_METEO_GEO,
            host="open-meteo-geo",
            params={"name": name, "count": 5, "language": "en", "format": "json"},
        )
    except ToolError:
        return None
    results = data.get("results") or []
    if not results:
        return None
    chosen = results[0]
    if hint:
        for r in results:
            if hint in (r.get("country", "").lower(), (r.get("country_code") or "").lower()):
                chosen = r
                break
    return {
        "query": query,
        "name": ", ".join(
            x for x in [chosen.get("name"), chosen.get("admin1"), chosen.get("country")] if x
        ),
        "lat": float(chosen["latitude"]),
        "lng": float(chosen["longitude"]),
        "country": chosen.get("country"),
        "country_code": (chosen.get("country_code") or "").upper(),
        "type": chosen.get("feature_code"),
    }


async def _nominatim(query: str) -> dict | None:
    s = get_settings()
    try:
        data = await http_client.get_json(
            _NOMINATIM,
            host="nominatim",
            params={"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1},
            headers={"User-Agent": s.nominatim_user_agent, "Accept-Language": "en"},
        )
    except ToolError:
        return None
    if not data:
        return None
    top = data[0]
    addr = top.get("address", {})
    return {
        "query": query,
        "name": top.get("display_name", query),
        "lat": float(top["lat"]),
        "lng": float(top["lon"]),
        "country": addr.get("country"),
        "country_code": (addr.get("country_code") or "").upper(),
        "type": top.get("type"),
    }


@tool(response_format="content_and_artifact")
async def geocode_place(query: str) -> tuple[str, dict]:
    """Resolve a place name (city, landmark, region) to coordinates and country.

    Use this first to anchor a destination before fetching weather or points of
    interest. Input: a place name like "Kyoto, Japan" or "Banff National Park".
    """
    result = await _open_meteo(query) or await _nominatim(query)
    if not result:
        return (f"No location found for {query!r}.", {"error": "not_found", "query": query})
    summary = (
        f"{result['name']} -> lat {result['lat']:.4f}, lng {result['lng']:.4f}"
        f" ({result.get('country') or 'unknown country'})"
    )
    return (summary, result)
