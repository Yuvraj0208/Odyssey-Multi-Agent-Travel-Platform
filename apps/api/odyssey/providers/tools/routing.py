"""Travel-time routing via OSRM (public server, no key), with a haversine fallback.

plan_day_route takes a day's ordered stops and returns per-leg walking durations so
the Logistics agent can validate that a day is physically doable. Real routing when
OSRM answers; a distance-based estimate when it does not, so logistics never fails.
"""

from __future__ import annotations

import math

from langchain_core.tools import tool

from odyssey.providers.http import ToolError, http_client

_OSRM = "http://router.project-osrm.org/route/v1"
_WALK_MPS = 1.35  # ~4.9 km/h
_DRIVE_MPS = 8.3  # ~30 km/h city


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371.0
    lat1, lng1 = math.radians(a[0]), math.radians(a[1])
    lat2, lng2 = math.radians(b[0]), math.radians(b[1])
    d = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(d))


def _fallback(coords: list[list[float]], mode: str) -> dict:
    speed = _DRIVE_MPS if mode == "driving" else _WALK_MPS
    legs = []
    total_min = total_km = 0.0
    for i in range(len(coords) - 1):
        a = (coords[i][1], coords[i][0])  # coords are [lng, lat]
        b = (coords[i + 1][1], coords[i + 1][0])
        km = _haversine_km(a, b) * 1.3  # road factor
        mins = (km * 1000 / speed) / 60
        legs.append({"duration_min": round(mins, 1), "distance_km": round(km, 2)})
        total_min += mins
        total_km += km
    return {
        "mode": mode,
        "source": "estimate",
        "legs": legs,
        "total_min": round(total_min, 1),
        "total_km": round(total_km, 2),
    }


@tool(response_format="content_and_artifact")
async def plan_day_route(coords: list[list[float]], mode: str = "walking") -> tuple[str, dict]:
    """Compute travel time and distance between a day's ordered stops.

    coords is a list of [lng, lat] pairs in visiting order. Returns per-leg and total
    walking (or driving) duration so a day's timing can be validated.
    """
    if not coords or len(coords) < 2:
        return ("Not enough stops to route.", {"legs": [], "total_min": 0.0, "total_km": 0.0, "source": "none"})

    path = ";".join(f"{c[0]},{c[1]}" for c in coords)
    url = f"{_OSRM}/{mode}/{path}"
    try:
        data = await http_client.get_json(
            url, host="osrm", params={"overview": "false", "annotations": "duration,distance"}
        )
        route = (data.get("routes") or [None])[0]
        if not route:
            raise ToolError("no route")
        legs = [
            {"duration_min": round(leg["duration"] / 60, 1), "distance_km": round(leg["distance"] / 1000, 2)}
            for leg in route.get("legs", [])
        ]
        art = {
            "mode": mode,
            "source": "osrm",
            "legs": legs,
            "total_min": round(route["duration"] / 60, 1),
            "total_km": round(route["distance"] / 1000, 2),
        }
    except (ToolError, KeyError, IndexError):
        art = _fallback(coords, mode)

    summary = f"{len(art['legs'])} legs, {art['total_min']:.0f} min {mode} total ({art['total_km']:.1f} km) [{art['source']}]"
    return (summary, art)
