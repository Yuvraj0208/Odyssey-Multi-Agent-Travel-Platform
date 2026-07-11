# Odyssey

An agentic AI travel platform. A team of seven specialized LangGraph agents plans
trips collaboratively, grounded in real open tourism data, with the multi-agent
collaboration visible live on screen. Human-in-the-loop bookings, durable resumable
conversations, long-term memory, and proactive re-planning. Fully open source, runs
locally.

> Built in six phases (0-5). See PROGRESS.md for the live checklist, DECISIONS.md
> for every non-trivial choice, and AGENTS.md for the agent contracts.

## What it does

- Describe a trip in natural language and watch a **supervisor route work to
  specialists** (memory, destination intelligence, trip planner, logistics, booking,
  support) that call real tools and hand context to each other - visible live in a
  **mission-control node-graph**.
- See the itinerary build on an **interactive MapLibre map** and a **drag-to-reorder
  day-by-day timeline**, grounded in live open data (weather, points of interest,
  real walking times).
- **Approve any booking explicitly** before it is confirmed - a LangGraph
  `interrupt()` gate surfaces a clean approval card; nothing is charged until you say so.
- **Resume** a conversation exactly where it left off (checkpointing), with your
  **preferences remembered across sessions** (long-term memory).
- Get **proactive notifications** when conditions change (e.g. rain on an outdoor
  day) with one-click re-planning - event-driven, not request-response.
- **Sign in** to sync trips and preferences; every user route is rate-limited and
  guarded (input sanitization + PII redaction).
- **Full observability**: every agent step, tool call, token, cost, and latency.

## Architecture

```
                      Next.js 15 web app  (chat . map . drag timeline . mission-control . approval modal . auth)
                                   |  SSE UIEvent stream (agent_enter/token/tool_*/handoff/plan_updated/approval_required/...)
                                   v
   FastAPI (async)  ── auth (JWT) . rate limit . guardrails . /chat/stream . /resume . /reorder . /sessions . /memory . /metrics
                                   |
                                   v
                LangGraph StateGraph  (TravelState . Postgres|SQLite checkpointer . long-term store)
                                   |
        START -> Supervisor  (deterministic pipeline + LLM at the decision point)
                   |    |         |          |            |             |
               Memory  Destination Trip     Logistics   Booking ----> booking_confirm
              (recall) Intelligence Planner (OSRM)      (search)      (interrupt -> approve/decline)
                   |    |         |          |            |
                   v    v         v          v            v
     tools: Open-Meteo (weather+geocode) . Overpass (POIs) . OSRM (routing) . Nominatim
            mock Flight/Hotel/Activity providers behind Protocols (idempotent, inventory, re-quote)
                                   ^
                        Traveler Support  (grounded Q&A + cancellations via the same gate)

   Persistence: Postgres (stack) / SQLite (local)   Vectors: Qdrant / Chroma
   Cache + pub/sub: Redis / in-process              Tracing: Langfuse   Metrics: Prometheus   Logs: structlog
```

Agents are **loosely coupled**: each lives in its own module and registers itself in
`AGENT_REGISTRY`. The supervisor's routing is built from the registry, so adding an
agent is: write the module, call `register(...)`. No edits to the supervisor or peers.

### How the agents collaborate

1. **Supervisor** extracts a structured trip brief and drives a deterministic forward
   pipeline (memory -> research -> plan -> logistics), consulting the LLM at the
   completion point to decide "done" vs. re-engage a specialist for a follow-up.
2. **Memory** recalls the traveler's durable preferences and injects them into context.
3. **Destination Intelligence** (a real ReAct tool-calling subgraph) geocodes,
   fetches the weather forecast, and pulls matching real POIs.
4. **Trip Planner** produces a structured itinerary, attaching geo from the real POI
   list so venues are never hallucinated; it adapts to weather (indoor on rainy days).
5. **Logistics** computes real OSRM walking times between stops, annotates transit,
   and flags over-packed days.
6. **Booking** searches/prices across mock providers and stages bookings, then the
   `booking_confirm` gate pauses via `interrupt()` for explicit approval before
   confirming with idempotency keys.
7. **Traveler Support** answers questions grounded in the trip and routes
   cancellations through the same approval gate.

Every handoff and tool call is streamed to the UI, powering both the chat and the
live mission-control panel.

## Two run modes

Odyssey runs the same code two ways, selected by `ODYSSEY_MODE`:

| | `stack` (production) | `local` (low-resource dev) |
|---|---|---|
| Orchestration | docker compose | single `uvicorn` process |
| Checkpointer / store | Postgres | SQLite (persists) / in-process |
| Vectors | Qdrant | Chroma (or none) |
| Cache / pub-sub | Redis | in-process |
| Tracing | Langfuse | optional |

### Run the full stack (Docker)

```bash
cp .env.example .env          # set GROQ_API_KEY (or switch ODYSSEY_LLM_PROVIDER)
docker compose up --build
# web http://localhost:3000  api http://localhost:8000  langfuse http://localhost:3001
```

### Run locally without Docker

```bash
# Backend
cd apps/api
python -m venv .venv && . .venv/Scripts/activate      # macOS/Linux: bin/activate
pip install -e ".[dev,local,llm,auth]"
cp ../../.env.example ../../.env                       # set GROQ_API_KEY
python -m odyssey.db.seed                              # OpenFlights + knowledge (optional)
ODYSSEY_MODE=local uvicorn odyssey.main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/web && npm install && npm run dev             # http://localhost:3000
```

Health `:8000/health` . Readiness `:8000/ready` . Metrics `:8000/metrics` . API docs `:8000/docs`

## Swapping the LLM

All LLM access goes through `apps/api/odyssey/providers/llm_provider.py`. One env var:

```bash
ODYSSEY_LLM_PROVIDER=groq    ODYSSEY_LLM_MODEL=llama-3.3-70b-versatile   # default
ODYSSEY_LLM_PROVIDER=ollama  ODYSSEY_LLM_MODEL=qwen2.5:7b                # local weights
ODYSSEY_LLM_PROVIDER=openai  OPENAI_BASE_URL=...  OPENAI_API_KEY=...     # vLLM/TGI/OpenRouter
```

> Note: the Groq free tier is rate-limited (~100k tokens/day on the 70B model). For
> heavy testing switch to `llama-3.1-8b-instant` or a served endpoint.

## Testing, evals, CI

```bash
cd apps/api && pytest -q          # 37 tests (schemas, providers, agents, security, evals)
ruff check odyssey tests          # lint
python -m odyssey.evals.run       # golden-scenario evals (deterministic checks + LLM judge)
cd apps/web && npx tsc --noEmit && npm run build
```

GitHub Actions (`.github/workflows/ci.yml`) runs ruff, pyright, pytest, the web
typecheck + build, and a docker build on every push.

## Security & ops

- **Auth**: JWT sessions (bcrypt-hashed passwords). `AUTH_REQUIRED` gates enforcement;
  the demo works signed-out via an anon id.
- **Rate limiting**: per-user/IP token bucket on the API surface.
- **Guardrails**: input sanitization + PII redaction (email/phone/card/SSN) in logs.
- **Resilience**: every external tool has timeout + retry + a per-host circuit breaker;
  agents degrade gracefully (partial results / fallbacks) so one failure never crashes
  the graph. Mock booking providers are idempotent with limited inventory.

## Documentation

- PLAN.md - repo layout, run modes, phase roadmap
- DECISIONS.md - every choice + one line of reasoning
- PROGRESS.md - live checklist mapped to the phases and definition of done
- AGENTS.md - each agent's purpose, inputs, outputs, tools, and delegation rules

## License

MIT.
