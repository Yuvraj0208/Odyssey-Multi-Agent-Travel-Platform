# Odyssey - Progress

Legend: [x] done and verified, [~] in progress, [ ] not started.

## Definition of done (the six)

- [~] 1. Clean premium web app, start a conversation. (Workspace + chat done;
      sign-in/auth lands in Phase 5.)
- [x] 2. Describe a trip in natural language; a team of agents plans it live, with
      collaboration visible (handoffs, tool calls, results in mission-control).
- [x] 3. Beautiful itinerary on an interactive map + day-by-day timeline, grounded
      in real open tourism data (weather, POIs). (Premium polish continues Phase 4.)
- [ ] 4. Flight/hotel/activity options; explicit approval before any booking. (Phase 3)
- [~] 5. Resume the same conversation later (checkpointer verified); long-term
      preference memory lands in Phase 2.
- [~] 6. Runs locally (local mode verified); one-command docker + full tracing/
      metrics wired, end-to-end stack run pending a Docker host.

## Phase 0 - Foundations

- [x] Monorepo scaffold + directory tree
- [x] Planning docs (PLAN, DECISIONS, PROGRESS, AGENTS)
- [x] Root config: .env.example, .gitignore, docker-compose.yml, Makefile, README
- [x] Backend pyproject + venv + install (Python 3.14, cp314 wheels all present)
- [x] core/config (pydantic-settings, mode-aware)
- [x] core/logging (structlog JSON, correlation id)
- [x] core/telemetry (Prometheus /metrics + per-session accounting)
- [x] providers/llm_provider (groq | ollama | openai)
- [x] Langfuse callback wiring (guarded, optional)
- [x] FastAPI app + /health + /ready + /metrics
- [x] Verify: app boots, health/ready/metrics respond (200), structlog JSON logs
- [ ] Verify LLM responds end to end (needs Groq key - pending from user)
- [ ] Alembic migrations + DB models (deferred to Phase 3 when bookings persist)

## Phase 1 - Vertical slice

- [x] TravelState + reducers
- [x] Agent registry + Handoff protocol
- [x] Supervisor node (registry-driven routing + guardrails)
- [x] Trip Planning agent (structured output + real-POI geo attachment)
- [x] Destination Intelligence agent (ReAct tool-calling subgraph)
- [x] Tools: Open-Meteo geocoding+weather, Overpass POIs (verified live)
- [x] Checkpointer + store factories (local SQLite / stack Postgres)
- [x] SSE streaming endpoint (astream_events v2 -> UI events)
- [x] Resume endpoint / thread resume (state rehydration via /sessions/{id}/state)
- [x] Next.js chat UI with streaming (three-region workspace)
- [x] Itinerary render + MapLibre map (markers, bounds, selection sync)
- [x] Mission-control agent rail + telemetry (Phase 4 will elevate to node-graph)
- [x] Backend test suite (15 tests, deterministic core logic) passing
- [x] Verify LIVE (browser, real Groq): trip request -> supervisor routes ->
      destination intel (geocode + weather + 30 real POIs) -> planner builds
      grounded itinerary -> streamed wrap-up; handoffs + tool calls visible in
      mission-control activity feed; map markers + timeline; resume after reload

## Phase 2 - More agents + memory

- [ ] Logistics Coordinator agent
- [ ] Personalization/Memory agent
- [ ] Long-term memory (store + vectors, per-user namespace)
- [ ] Proactive re-planning (Redis pub/sub, weather trigger)

## Phase 3 - Bookings + HITL

- [ ] FlightProvider/HotelProvider/ActivityProvider Protocols + mocks
- [ ] Booking agent + idempotency
- [ ] Interrupt-based approval gate + resume
- [ ] Traveler Support agent
- [ ] UI: options cards, approval modal, pending vs confirmed

## Phase 4 - Premium UI + mission control

- [ ] Design language + three-region workspace
- [ ] Drag-to-reorder timeline -> re-validate logistics
- [ ] Live agent mission-control panel
- [ ] Real telemetry (tokens/cost/latency)
- [ ] Notifications inbox

## Phase 5 - Hardening

- [ ] Auth (JWT), rate limiting, guardrails
- [ ] Circuit breakers + graceful degradation across tools
- [ ] Tests + evals + GitHub Actions CI
- [ ] Seed scripts (OpenFlights + knowledge base)
- [ ] README with architecture diagram, final finish pass
