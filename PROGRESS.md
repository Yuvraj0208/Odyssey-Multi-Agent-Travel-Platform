# Odyssey - Progress

Legend: [x] done and verified, [~] in progress, [ ] not started.

## Definition of done (the six)

- [x] 1. Clean premium web app, sign in, start a conversation. (Auth verified live
      in Phase 5: register -> signed-in avatar; token-scoped trips + preferences.)
- [x] 2. Describe a trip in natural language; a team of agents plans it live, with
      collaboration visible (handoffs, tool calls, results in mission-control).
- [x] 3. Beautiful itinerary on an interactive map + day-by-day timeline, grounded
      in real open tourism data (weather, POIs). (Premium polish continues Phase 4.)
- [x] 4. Flight/hotel/activity options; explicit approval before any booking.
      (Phase 3, verified live: approval modal gates all confirmations.)
- [x] 5. Resume the same conversation later (checkpointer verified); long-term
      preference memory now recalls across sessions (Phase 2, verified live).
- [x] 6. Runs locally with verified tracing hooks, structlog, Prometheus metrics,
      37 tests. One-command `docker compose up` + Dockerfiles are in place; the
      end-to-end stack run needs a Docker host (absent on this build machine).

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

- [x] Logistics Coordinator agent (real OSRM walking times, transit annotations,
      per-day feasibility; haversine fallback)
- [x] Personalization/Memory agent (recall at start of planning, personalizes plan)
- [x] Long-term memory (LangGraph store, per-user namespace; keyword-ranked recall,
      Qdrant/embeddings drop-in seam); write salient facts on done
- [x] Deterministic forward pipeline (memory->research->plan->logistics) + LLM at
      the completion/follow-up decision point
- [x] Event bus (in-process local / Redis stack) + notification hub + weather
      coordinator; conditions monitor publishes weather_changed -> notification
- [x] Notifications: SSE stream + inbox bell + toasts + one-click re-plan; recheck
      endpoint (?demo=true to exercise the path when weather is benign)
- [x] 6 Phase-2 tests (21 total). Verified via script: memory persists + recalls
      across sessions; logistics OSRM timing; pipeline order
- [x] Verified LIVE in browser: 5-agent mission control; memory recall; OSRM
      transit legs + per-day feasibility; real weather re-check -> 2 proactive
      notifications (bell + toast) -> one-click re-plan routes to planner correctly

## Phase 3 - Bookings + HITL

- [x] Flight/Hotel/Activity Protocols + realistic mocks (latency, failures,
      re-quote pricing, limited inventory w/ lock, idempotent booking, cancel)
- [x] Provider registry (parallel search, merge, graceful degradation)
- [x] Booking agent (intent parse, search + price + stage) + idempotency keys
- [x] Interrupt-based approval gate (dynamic interrupt()) + resume_turn + resume endpoint
- [x] Traveler Support agent (grounded Q&A + cancellations through the gate)
- [x] Registry dynamic_routing (Command(goto) agents skip auto supervisor edge)
- [x] UI: options cards, approval modal, pending vs confirmed (Bookings panel)
- [x] 5 Phase-3 tests (26 total)
- [x] Verified LIVE in browser: book -> approval modal -> approve -> both confirmed
      with refs; decline books nothing; idempotency + inventory hold (7-agent MC)

## Phase 4 - Premium UI + mission control

- [x] Design language + three-region workspace (refined; focus rings, selection)
- [x] Drag-to-reorder timeline (Framer Reorder) -> POST /reorder re-validates
      logistics timing deterministically (OSRM, no LLM)
- [x] Live agent mission-control NODE-GRAPH: agents as nodes, active nodes pulse,
      handoffs animate a dot traveling along the connector, real telemetry
- [x] Real telemetry (tokens/cost/latency) - latency now populated per turn
- [x] Notifications inbox (Phase 2) + Trips history + Preferences slide-over
      (store-backed sessions index + memory CRUD API)
- [x] Verified LIVE in browser: node-graph renders 7 agents with done-checkmarks +
      latency (32s); drag-to-reorder reorders + re-validates OSRM transit + persists
      across reload (fixed aupdate_state as_node bug); trips + preferences panels

## Phase 5 - Hardening

- [x] Auth (JWT + bcrypt): register/login/me, current_user JWT-or-x-user-id, gated
      by AUTH_REQUIRED; frontend sign in/up + token-authenticated API. Verified live.
- [x] Rate limiting (per-user/IP token bucket middleware on /api)
- [x] Guardrails: input sanitization + PII redaction (structlog processor)
- [x] Circuit breakers (per-host, in http client) + graceful degradation across all
      tools + agents (verified through Phases 1-3)
- [x] Tests (37) + eval harness (deterministic checks + LLM judge + golden scenarios)
      + GitHub Actions CI (ruff, pyright, pytest, tsc, next build, docker build)
- [x] Seed script (downloads 6072 OpenFlights airports + starter knowledge set)
- [x] Dockerfiles (api + web); README with architecture diagram + finish pass
