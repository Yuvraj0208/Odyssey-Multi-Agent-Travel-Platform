# Odyssey - Decision Log

One line of reasoning per choice. Newest at the bottom of each section.

## Environment / run model

- Two run modes (stack + local) behind mode-aware factories. Reason: the build
  machine has no Docker and ~1GB free RAM, but the spec requires a full compose
  stack; building both keeps the spec deliverable real while staying verifiable
  here. One code path, mode chosen by env var.
- Python: use psycopg3 (binary wheels) and aiosqlite (pure Python), avoid asyncpg.
  Reason: the machine runs Python 3.14, where asyncpg may lack wheels; psycopg3
  and aiosqlite install cleanly and both LangGraph checkpointers support them.

## LLM

- Default running provider: Groq (ChatGroq), model llama-3.3-70b-versatile.
  Reason: local Ollama is broken and there is not enough RAM for a local model;
  Groq is open-weights, OpenAI-compatible, free tier, strong tool calling. Kept
  swappable via ODYSSEY_LLM_PROVIDER (groq | ollama | openai).
- Provider abstraction returns a LangChain BaseChatModel so tool binding,
  streaming, and astream_events work identically across providers.

## Orchestration

- LangGraph StateGraph with one subgraph per specialist and a custom supervisor
  node. Reason: the spec wants full control over routing and the UI trace stream;
  a custom supervisor lets us emit typed handoff events for mission-control.
- Routing is registry-driven: the supervisor prompt is assembled from agent
  descriptions in AGENT_REGISTRY. Reason: adding an agent must not require editing
  the supervisor or peers (loose coupling requirement).

## State / persistence

- Checkpointer: AsyncPostgresSaver (stack) / AsyncSqliteSaver (local), keyed by
  thread_id = session_id. Reason: durable, resumable threads; SQLite still
  persists to a file so resume-after-restart works locally.
- Long-term memory store: AsyncPostgresStore (stack) / in-process store (local),
  namespaced per user_id. Reason: cross-session semantic memory per the spec.

## Knowledge / vectors

- Vector store behind a repository interface: Qdrant (stack) / Chroma (local).
  Reason: swappable per spec; Chroma needs no server for local dev.
- Embeddings: fastembed (ONNX, CPU) rather than sentence-transformers (torch).
  Reason: low RAM; fastembed ships small quantized models and no torch dependency.
  RAG is optional in Phase 1 and degrades gracefully if embeddings are unavailable.

## Streaming

- graph.astream_events(version="v2") mapped to a compact UI event schema over SSE
  (sse-starlette). Reason: single event feed powers both chat and mission-control;
  SSE is simpler than WebSocket for one-directional server push and resumes well.

## Tools / data sources (Phase 1)

- Weather: Open-Meteo (no key). POIs: OpenTripMap (free key) with an Overpass API
  fallback (no key). Geocoding: Nominatim (OSM). Reason: all open, no paid source;
  Overpass fallback means POIs still work with zero keys configured.

## Frontend

- Next.js 15 App Router + React 19 + TS, Tailwind + shadcn/ui, Framer Motion,
  MapLibre GL + OpenFreeMap tiles (no key), TanStack Query, Zustand, react-hook-form
  + zod. Reason: exactly the spec stack; all open and keyless for maps.
