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

## Phase 1 runtime fixes (learned by running)

- Geocoding: Open-Meteo geocoding API is the PRIMARY, Nominatim the fallback.
  Reason: Nominatim returns 403 to non-browser/app user agents and rate-limits
  hard; Open-Meteo geocoding is keyless, reliable, and same-provider as weather.
- Overpass: POST the query as form body, send an app-identifying User-Agent, and
  round-robin four public mirrors with a PER-MIRROR circuit breaker. Reason: the
  default python-httpx UA gets 406, and a single shared breaker would let one bad
  mirror block the others.
- Dark basemap: invert only the MapLibre WebGL canvas via CSS filter. Reason:
  OpenFreeMap has no official dark style; HTML markers/popups are siblings of the
  canvas so they stay upright and correctly colored.
- SSE consumed via fetch + ReadableStream reader, not EventSource. Reason: the
  chat stream endpoint is a POST (carries the message body); EventSource is GET-only.
- Langgraph/langchain resolved to 1.x (not the spec's 0.2.x). Kept astream_events
  version="v2" (still supported) and used create_react_agent(state_schema=...) plus
  tag-based per-agent attribution for the stream mapper.

## Phase 2 (memory, logistics, proactive)

- Routing is a deterministic forward pipeline (memory -> research -> plan ->
  logistics), with the LLM deciding only at the completion point (done vs. a
  follow-up re-engage). Reason: pure LLM routing skipped memory and double-ran
  logistics; a fixed pipeline guarantees order + termination while the agents' real
  work (and the LLM's follow-up/clarify decisions) keep it genuinely agentic.
- Long-term memory uses the LangGraph store with keyword-overlap ranking rather than
  embeddings. Reason: fastembed/onnxruntime is heavy and risky on py3.14 + low RAM;
  keyword recall is robust and the ranking function is the single swap point for
  Qdrant/vectors later.
- Memory read is an agent node (visible in mission-control); memory write is a
  helper the supervisor calls on done. Reason: reads should personalize downstream
  agents (so they run first, as a node), writes are an end-of-turn side effect.
- Logistics is advisory (annotates transit + flags over-packed days) rather than
  auto-rewriting the plan. Reason: keeps turns bounded and avoids planner<->logistics
  loops; the delegate-back handoff remains available for a future iteration.
- Travel times via OSRM public server (one call per day using waypoint legs),
  haversine estimate fallback. Reason: real durations, keyless, resilient.
- Proactive re-planning: event bus (in-process local / Redis stack) + a background
  weather coordinator that turns weather_changed events into user notifications
  streamed over SSE. A ?demo=true flag on recheck exercises the full path when live
  weather is benign. Reason: genuinely event-driven, not a poll baked into the turn.

## Phase 3 (bookings, human-in-the-loop)

- HITL approval uses a dynamic interrupt() inside a booking_confirm node, not the
  spec's static interrupt_before. Reason: dynamic interrupt passes the rich approval
  payload out and the decision back in cleanly; search/confirm are split into two
  nodes so staged bookings are committed to state before the pause (resume re-runs
  only the confirm step, so no double search).
- Agents that route via Command(goto=...) set AgentSpec.dynamic_routing=True and the
  build skips their automatic edge to the supervisor. Reason: a Command goto plus a
  static edge both fire, racing writes to shared state keys (InvalidUpdateError).
- confirmed_bookings is last-writer-wins (full list managed in booking_confirm) so
  cancellations can flip an existing booking's status; pending_bookings is cleared on
  confirm/decline. Idempotency keys are generated at stage time and reused on confirm.
- Mock providers only; traveler is a placeholder ("Guest Traveler") - no real PII or
  payment is ever collected, matching the "never enter financial/PII" safety rule.
- Booking search/confirm/cancel are wrapped as LangChain tools so provider calls show
  natively in mission-control (same pattern as the other agents' tools).

## Frontend

- Next.js 15 App Router + React 19 + TS, Tailwind + shadcn/ui, Framer Motion,
  MapLibre GL + OpenFreeMap tiles (no key), TanStack Query, Zustand, react-hook-form
  + zod. Reason: exactly the spec stack; all open and keyless for maps.
