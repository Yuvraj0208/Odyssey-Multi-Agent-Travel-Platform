# Odyssey

An agentic AI travel platform. A team of specialized LangGraph agents plans trips
collaboratively, grounded in real open tourism data, with the multi-agent
collaboration visible live on screen. Human-in-the-loop bookings, durable
resumable conversations, and long-term memory. Fully open source.

> Status: in active phased build. See PROGRESS.md for what is done. This README
> documents the target architecture and both run modes.

## What it does

- Describe a trip in natural language and watch a supervisor route work to
  specialists (trip planner, destination intelligence, logistics, booking,
  support) that call real tools and hand context to each other.
- See the itinerary build up on an interactive map and a day-by-day timeline,
  grounded in live open data (weather, points of interest, destination info).
- Approve any booking explicitly before it is confirmed (human-in-the-loop via
  LangGraph interrupts).
- Resume a conversation later exactly where it left off (checkpointing) with your
  preferences remembered across sessions (long-term memory).
- Full observability: every agent step, tool call, token, latency, and cost.

## Architecture

```
                         Next.js 15 web app (chat + map + timeline + mission control)
                                        |  SSE (UI event stream)
                                        v
   FastAPI (async)  ---- /api/chat/{session}/stream, /resume, /trips, /sessions, /health, /metrics
                                        |
                                        v
                LangGraph StateGraph (TravelState, checkpointer, store)
                                        |
             +--------------------------+--------------------------+
             |            Supervisor (registry-driven routing)     |
             +--------------------------+--------------------------+
              |            |              |            |           |
        Trip Planner  Destination   Logistics    Booking     Traveler
                      Intelligence  Coordinator  (HITL gate)  Support
              |            |              |            |
              v            v              v            v
        tools: Open-Meteo, OpenTripMap/Overpass, Nominatim, Wikivoyage,
               REST Countries, mock flight/hotel/activity providers (Protocol seam)

  Persistence: Postgres (stack) / SQLite (local)  | Vectors: Qdrant / Chroma
  Cache + pub/sub: Redis  | Tracing: Langfuse  | Metrics: Prometheus  | Logs: structlog
```

The agents are loosely coupled: each lives in its own module and registers itself
in `AGENT_REGISTRY`. The supervisor's routing prompt is built from the registry
descriptions, so adding an agent is: write the module, call `register(...)`. No
edits to the supervisor or peers. See AGENTS.md.

## Two run modes

Odyssey runs the same code two ways, selected by `ODYSSEY_MODE`:

| | `stack` (production) | `local` (low-resource dev) |
|---|---|---|
| Orchestration | docker compose | single `uvicorn` process |
| Checkpointer | Postgres | SQLite (persists to file) |
| Long-term store | Postgres | in-process |
| Vectors | Qdrant | Chroma (or none) |
| Cache / pub-sub | Redis | in-process |
| Tracing | Langfuse | optional |

### Run the full stack (Docker)

```bash
cp .env.example .env          # set GROQ_API_KEY (or switch ODYSSEY_LLM_PROVIDER)
docker compose up --build
# web: http://localhost:3000  api: http://localhost:8000  langfuse: http://localhost:3001
```

### Run locally without Docker (low RAM)

```bash
# Backend
cd apps/api
python -m venv .venv && . .venv/Scripts/activate      # macOS/Linux: bin/activate
pip install -e ".[dev,local,llm]"
cp ../../.env.example ../../.env                       # set GROQ_API_KEY
ODYSSEY_MODE=local uvicorn odyssey.main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/web
npm install
npm run dev                                            # http://localhost:3000
```

## Swapping the LLM

All LLM access goes through `apps/api/odyssey/providers/llm_provider.py`. Change
one env var:

```bash
ODYSSEY_LLM_PROVIDER=groq    ODYSSEY_LLM_MODEL=llama-3.3-70b-versatile   # default
ODYSSEY_LLM_PROVIDER=ollama  ODYSSEY_LLM_MODEL=qwen2.5:7b                # local weights
ODYSSEY_LLM_PROVIDER=openai  OPENAI_BASE_URL=...  OPENAI_API_KEY=...     # vLLM/TGI/OpenRouter
```

## Documentation

- PLAN.md - repo layout, run modes, phase roadmap.
- DECISIONS.md - every non-trivial choice and one line of reasoning.
- PROGRESS.md - live checklist mapped to phases and the definition of done.
- AGENTS.md - each agent's purpose, inputs, outputs, tools, and delegation rules.

## License

MIT.
