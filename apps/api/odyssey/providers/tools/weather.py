"""Weather via Open-Meteo (no key).

Returns a daily forecast for the requested window. Open-Meteo provides ~16 days of
forecast; for dates beyond that we return the nearest available forecast and flag
it, so downstream planning can note "seasonal estimate" rather than fail.
"""

from __future__ import annotations

from datetime import date, timedelta

from langchain_core.tools import tool

from odyssey.providers.http import ToolError, http_client

_FORECAST = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes -> short human labels.
_WMO = {
    0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "rime fog", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 66: "freezing rain", 67: "freezing rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains",
    80: "rain showers", 81: "rain showers", 82: "violent rain showers",
    85: "snow showers", 86: "snow showers", 95: "thunderstorm",
    96: "thunderstorm w/ hail", 99: "thunderstorm w/ hail",
}


def _label(code: int | None) -> str:
    return _WMO.get(int(code), "unknown") if code is not None else "unknown"


@tool(response_format="content_and_artifact")
async def get_weather(
    lat: float,
    lng: float,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[str, dict]:
    """Get a daily weather forecast for a coordinate and optional date window.

    Dates are ISO strings (YYYY-MM-DD). Use this to decide which days suit outdoor
    vs indoor activities. If the window is beyond the forecast horizon, results are
    flagged as a seasonal estimate.
    """
    params: dict = {
        "latitude": lat,
        "longitude": lng,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
    }
    today = date.today()
    horizon = today + timedelta(days=16)
    estimate = False
    if start_date and end_date:
        try:
            sd, ed = date.fromisoformat(start_date), date.fromisoformat(end_date)
            # Open-Meteo's forecast endpoint only covers [today, today+16]. Anything
            # in the past or beyond the horizon becomes a seasonal estimate rather
            # than a 400 error.
            if sd < today or sd > horizon:
                estimate = True
                params["forecast_days"] = 7
            else:
                params["start_date"] = max(sd, today).isoformat()
                params["end_date"] = min(ed, horizon).isoformat()
        except ValueError:
            params["forecast_days"] = 7
    else:
        params["forecast_days"] = 7

    try:
        data = await http_client.get_json(_FORECAST, host="open-meteo", params=params)
    except ToolError as e:
        return (f"Weather unavailable: {e}", {"error": str(e)})

    daily = data.get("daily", {})
    days = []
    for i, d in enumerate(daily.get("time", [])):
        days.append(
            {
                "date": d,
                "condition": _label(daily.get("weathercode", [None])[i]),
                "temp_max_c": daily.get("temperature_2m_max", [None])[i],
                "temp_min_c": daily.get("temperature_2m_min", [None])[i],
                "precip_prob_pct": daily.get("precipitation_probability_max", [None])[i],
            }
        )

    if not days:
        return ("No forecast data returned.", {"error": "empty", "days": []})

    rainy = [d["date"] for d in days if (d["precip_prob_pct"] or 0) >= 60]
    head = "Seasonal estimate" if estimate else "Forecast"
    summary = (
        f"{head}: {len(days)} days, "
        + ", ".join(f"{d['date']} {d['condition']} {d['temp_min_c']}-{d['temp_max_c']}C" for d in days[:5])
        + (f" | high rain risk: {', '.join(rainy)}" if rainy else "")
    )
    return (summary, {"estimate": estimate, "days": days, "rainy_days": rainy})
