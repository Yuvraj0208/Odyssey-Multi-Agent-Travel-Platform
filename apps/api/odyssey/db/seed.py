"""Seed script: OpenFlights airports + a starter destination knowledge set.

    python -m odyssey.db.seed

Downloads the open OpenFlights airports dataset and writes a filtered airports
reference (IATA -> geo) plus a small curated destination knowledge set under ./data.
In stack mode the same records are upserted into Qdrant behind the knowledge
repository; locally they are JSON the agents/tools can read without a server.
"""

from __future__ import annotations

import asyncio
import csv
import io

from odyssey.core.config import get_settings
from odyssey.core.logging import get_logger

log = get_logger(__name__)

_OPENFLIGHTS = (
    "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
)

# Fallback so `make seed` works fully offline.
_FALLBACK_AIRPORTS = [
    {"iata": "LIS", "name": "Humberto Delgado", "city": "Lisbon", "country": "Portugal", "lat": 38.7813, "lng": -9.1359},
    {"iata": "BCN", "name": "Barcelona El Prat", "city": "Barcelona", "country": "Spain", "lat": 41.2971, "lng": 2.0785},
    {"iata": "KIX", "name": "Kansai Intl", "city": "Osaka", "country": "Japan", "lat": 34.4273, "lng": 135.2440},
    {"iata": "LHR", "name": "Heathrow", "city": "London", "country": "United Kingdom", "lat": 51.4706, "lng": -0.4619},
]

_KNOWLEDGE = [
    {"destination": "Kyoto", "text": "Kyoto is Japan's temple capital: Kinkaku-ji, Fushimi Inari, and the Arashiyama bamboo grove. Best in spring (cherry blossoms) and autumn (foliage). Compact and walkable with an easy bus/subway network."},
    {"destination": "Lisbon", "text": "Lisbon is a hilly coastal capital of miradouros (viewpoints), historic trams, and pastel de nata. Belem, Alfama, and Bairro Alto are the classic neighborhoods. Mild most of the year."},
    {"destination": "Barcelona", "text": "Barcelona pairs Gaudi modernism (Sagrada Familia, Park Guell) with a Gothic Quarter, tapas, and a city beach at Barceloneta. Walkable core; metro reaches the rest."},
]


def _parse_airports(text: str) -> list[dict]:
    airports = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        # OpenFlights: id,name,city,country,iata,icao,lat,lng,...
        if len(row) < 8:
            continue
        iata = row[4].strip()
        if not iata or iata == "\\N" or len(iata) != 3:
            continue
        try:
            lat, lng = float(row[6]), float(row[7])
        except ValueError:
            continue
        airports.append({"iata": iata, "name": row[1], "city": row[2], "country": row[3], "lat": lat, "lng": lng})
    return airports


async def seed() -> None:
    s = get_settings()
    data_dir = s.resolve_path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    airports: list[dict]
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30) as c:
            resp = await c.get(_OPENFLIGHTS, headers={"User-Agent": "OdysseyTravel/0.1"})
            resp.raise_for_status()
            airports = _parse_airports(resp.text)
        log.info("seed.airports_downloaded", count=len(airports))
    except Exception as e:
        log.warning("seed.airports_fallback", error=str(e))
        airports = _FALLBACK_AIRPORTS

    import orjson

    (data_dir / "airports.json").write_bytes(orjson.dumps(airports))
    (data_dir / "knowledge.json").write_bytes(orjson.dumps(_KNOWLEDGE))

    # In stack mode, also upsert the knowledge set into the vector store.
    if not s.is_local and s.vector_backend == "qdrant":
        try:
            from odyssey.knowledge.repository import get_knowledge_repo

            repo = get_knowledge_repo()
            await repo.upsert_destinations(_KNOWLEDGE)
            log.info("seed.knowledge_upserted", count=len(_KNOWLEDGE))
        except Exception as e:  # pragma: no cover
            log.warning("seed.knowledge_skip", error=str(e))

    print(f"Seeded {len(airports)} airports and {len(_KNOWLEDGE)} destination notes into {data_dir}")


if __name__ == "__main__":
    asyncio.run(seed())
