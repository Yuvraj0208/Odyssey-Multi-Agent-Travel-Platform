# Odyssey - Build Plan

Odyssey is a production-grade agentic AI travel platform: a team of specialized
LangGraph agents that plan trips collaboratively, grounded in real open tourism
data, with the multi-agent collaboration visible live on screen, human-in-the-loop
bookings, durable resumable conversations, and long-term memory.

This document is the working plan. It is updated as phases complete. See
DECISIONS.md for choices and reasoning, PROGRESS.md for the live checklist, and
AGENTS.md for the agent contracts.

## Repo layout

```
AG-AI-Tourism/                 (repo root, codename "odyssey")
  docker-compose.yml           full stack: postgres, redis, qdrant, langfuse, api, web
  Makefile                     dev / migrate / seed / test / lint / down
  README.md                    architecture + how to run + how to swap the LLM
  PLAN.md  DECISIONS.md  PROGRESS.md  AGENTS.md
  .env.example
  apps/
    api/                       FastAPI backend (async)
      odyssey/
        agents/                one module per agent + supervisor + registry
        graph/                 TravelState, graph assembly, checkpointer, store, streaming
        providers/             external tool clients + mock booking providers (Protocol seam)
        knowledge/             vector store repo interface, ingestion, retrieval
        memory/                long-term semantic memory
        api/                   FastAPI routers: auth, chat stream, trips, bookings, memory, health
        core/                  config, logging, telemetry, guardrails, security
        db/                    sqlalchemy models + alembic
        schemas/               pydantic contracts (shared)
        prompts/               versioned agent prompts
      tests/
      pyproject.toml
    web/                       Next.js 15 + React 19 + TS frontend
      src/app  src/components  src/lib  src/hooks  src/styles
      package.json
  infra/                       prometheus config, langfuse config, seed scripts
  packages/                    optional shared types/config
```

## Two run modes (decided with the user)

The machine used to build this has no Docker and limited RAM, so Odyssey targets
two interchangeable run modes behind the same code:

1. Production / spec stack (`ODYSSEY_MODE=stack`): docker compose brings up
   postgres, redis, qdrant, langfuse, api, web. LangGraph uses the Postgres
   checkpointer + store, Qdrant for vectors.
2. Local dev (`ODYSSEY_MODE=local`): single backend process, no Docker. SQLite
   checkpointer (persists to a file so resume-after-restart still works), an
   in-process store, Chroma or in-memory vector store. This is what we verify on
   the build machine.

The seam is a set of factory functions in `graph/` and `knowledge/` that read
`ODYSSEY_MODE` and return the right implementation. Agents never know which mode
they run in.

## LLM

All LLM access goes through `providers/llm_provider.py`. One env var
(`ODYSSEY_LLM_PROVIDER`) switches between:
- `groq`  -> ChatGroq (default for running; Llama 3.3 70B, strong tool calling)
- `ollama` -> ChatOllama (local open weights, when hardware allows)
- `openai` -> ChatOpenAI with a custom base_url (vLLM / TGI / OpenRouter / Together)

No client is hardcoded anywhere else.

## Phase order (build, run, verify each before the next)

- Phase 0  Foundations: scaffold, compose, env/config, structlog, health/ready,
  Alembic, base schemas, llm_provider, Langfuse wiring. Verify services + LLM.
- Phase 1  Vertical slice: Supervisor + Trip Planner + Destination Intelligence
  as subgraphs; shared state; checkpointer; SSE streaming; real Open-Meteo +
  OpenTripMap tools; Next.js chat with streaming + itinerary + MapLibre map;
  resume after restart.
- Phase 2  Logistics + Personalization/Memory agents; long-term memory (store +
  vectors); proactive re-planning via Redis pub/sub (weather trigger).
- Phase 3  Booking Agent + mock flight/hotel/activity providers; idempotency;
  interrupt-based approval gate + resume endpoint; Traveler Support agent.
- Phase 4  Premium UI: three-region workspace, drag-to-reorder timeline, the live
  agent mission-control panel, real telemetry, notifications inbox.
- Phase 5  Hardening: auth, rate limiting, guardrails, circuit breakers, tests +
  evals + CI, seed scripts, README with diagram, final finish pass.

## Starting now: Phase 0, then Phase 1

First files:
1. Planning docs (this file, DECISIONS.md, PROGRESS.md, AGENTS.md).
2. Root: .env.example, .gitignore, docker-compose.yml, Makefile, README.md.
3. Backend Phase 0: pyproject.toml, core/config.py, core/logging.py,
   core/telemetry.py, providers/llm_provider.py, schemas/base, api/health, main app.
4. Verify: create venv, install, boot the API, hit /health and /ready.
5. Phase 1: TravelState + registry + supervisor + two agents + tools + streaming +
   Next.js slice. Verify a trip request end to end.
