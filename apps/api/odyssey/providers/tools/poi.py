"""Points of interest via OpenStreetMap Overpass API (no key required).

Interests (free text) are mapped to OSM tag selectors, so "temples and food" pulls
places of worship and restaurants near the destination. OpenTripMap can be layered
in later behind the same tool if OPENTRIPMAP_API_KEY is set; Overpass keeps Odyssey
fully keyless out of the box.
"""

from __future__ import annotations

from urllib.parse import urlparse

from langchain_core.tools import tool

from odyssey.providers.http import ToolError, http_client

# Multiple public Overpass mirrors for resilience; tried in order until one answers.
_OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# interest keyword -> list of Overpass selectors and a display category
_INTEREST_MAP: dict[str, tuple[list[str], str]] = {
    "temple": (['["amenity"="place_of_worship"]', '["historic"="temple"]'], "spiritual"),
    "shrine": (['["amenity"="place_of_worship"]'], "spiritual"),
    "religious": (['["amenity"="place_of_worship"]'], "spiritual"),
    "museum": (['["tourism"="museum"]'], "culture"),
    "art": (['["tourism"="gallery"]', '["tourism"="museum"]'], "culture"),
    "history": (['["historic"]'], "history"),
    "heritage": (['["historic"]'], "history"),
    "castle": (['["historic"="castle"]'], "history"),
    "food": (['["amenity"="restaurant"]'], "food"),
    "dining": (['["amenity"="restaurant"]'], "food"),
    "cafe": (['["amenity"="cafe"]'], "food"),
    "coffee": (['["amenity"="cafe"]'], "food"),
    "nature": (['["leisure"="park"]', '["natural"="peak"]'], "nature"),
    "park": (['["leisure"="park"]'], "nature"),
    "hiking": (['["natural"="peak"]', '["tourism"="viewpoint"]'], "nature"),
    "outdoor": (['["leisure"="park"]', '["tourism"="viewpoint"]'], "nature"),
    "scenic": (['["tourism"="viewpoint"]'], "nature"),
    "viewpoint": (['["tourism"="viewpoint"]'], "nature"),
    "beach": (['["natural"="beach"]'], "nature"),
    "nightlife": (['["amenity"="bar"]', '["amenity"="pub"]'], "nightlife"),
    "bar": (['["amenity"="bar"]'], "nightlife"),
    "shopping": (['["shop"="mall"]', '["amenity"="marketplace"]'], "shopping"),
    "market": (['["amenity"="marketplace"]'], "shopping"),
}

# Always include these so iconic sights show up regardless of interests.
_BASE_SELECTORS = [('["tourism"="attraction"]', "attraction"), ('["tourism"="viewpoint"]', "nature")]


def _selectors_for(interests: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = list(_BASE_SELECTORS)
    seen = {s for s, _ in out}
    for raw in interests:
        key = raw.lower().strip()
        for kw, (sels, cat) in _INTEREST_MAP.items():
            if kw in key:
                for s in sels:
                    if s not in seen:
                        out.append((s, cat))
                        seen.add(s)
    return out


def _build_query(lat: float, lng: float, radius_m: int, selectors: list[tuple[str, str]]) -> str:
    parts = []
    for sel, _cat in selectors:
        parts.append(f'  node{sel}(around:{radius_m},{lat},{lng});')
        parts.append(f'  way{sel}(around:{radius_m},{lat},{lng});')
    body = "\n".join(parts)
    return f"[out:json][timeout:25];\n(\n{body}\n);\nout center 60;"


@tool(response_format="content_and_artifact")
async def search_pois(
    lat: float,
    lng: float,
    interests: list[str] | None = None,
    radius_m: int = 8000,
    limit: int = 30,
) -> tuple[str, dict]:
    """Find real points of interest near a coordinate, matched to traveler interests.

    Pass the destination coordinates and a list of interests like
    ["temples", "food", "museums"]. Returns named places with coordinates and a
    category, drawn from OpenStreetMap. Always includes top attractions.
    """
    interests = interests or []
    selectors = _selectors_for(interests)
    cat_by_sel = {sel: cat for sel, cat in selectors}
    query = _build_query(lat, lng, radius_m, selectors)

    data = None
    last_err: str | None = None
    for endpoint in _OVERPASS_ENDPOINTS:
        try:
            # Overpass expects the query POSTed as form data ("data=..."). Breaker
            # is keyed per-mirror so one failing mirror never blocks the others.
            data = await http_client.post_json(
                endpoint, host=urlparse(endpoint).netloc, data={"data": query}
            )
            break
        except ToolError as e:
            last_err = str(e)
            continue
    if data is None:
        return (f"POI search unavailable: {last_err}", {"error": last_err, "pois": []})

    pois = []
    seen_names = set()
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        if not name or name in seen_names:
            continue
        if el["type"] == "node":
            plat, plng = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            plat, plng = center.get("lat"), center.get("lon")
        if plat is None or plng is None:
            continue
        # infer category from matching tag
        kind = (
            tags.get("tourism")
            or tags.get("amenity")
            or tags.get("historic")
            or tags.get("leisure")
            or tags.get("natural")
            or tags.get("shop")
            or "attraction"
        )
        seen_names.add(name)
        pois.append(
            {
                "name": name,
                "lat": plat,
                "lng": plng,
                "kind": kind,
                "category": _category_for(kind),
                "cuisine": tags.get("cuisine"),
            }
        )
        if len(pois) >= limit:
            break

    if not pois:
        return ("No points of interest found nearby.", {"pois": [], "count": 0})

    by_cat: dict[str, int] = {}
    for p in pois:
        by_cat[p["category"]] = by_cat.get(p["category"], 0) + 1
    summary = f"Found {len(pois)} POIs: " + ", ".join(f"{n} {c}" for c, n in by_cat.items())
    return (summary, {"pois": pois, "count": len(pois)})


_KIND_CATEGORY = {
    "place_of_worship": "spiritual", "temple": "spiritual",
    "museum": "culture", "gallery": "culture", "artwork": "culture",
    "castle": "history", "monument": "history", "memorial": "history", "ruins": "history",
    "restaurant": "food", "cafe": "food", "marketplace": "shopping", "mall": "shopping",
    "park": "nature", "peak": "nature", "viewpoint": "nature", "beach": "nature",
    "bar": "nightlife", "pub": "nightlife",
    "attraction": "attraction",
}


def _category_for(kind: str) -> str:
    return _KIND_CATEGORY.get(kind, "attraction")
