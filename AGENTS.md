# Odyssey - Agents

Odyssey uses a Supervisor/Orchestrator plus specialist agents. Each specialist is
its own LangGraph subgraph, registers itself in AGENT_REGISTRY, reads and writes a
single shared typed state (TravelState), and returns control to the supervisor.
Adding an agent means writing a module and calling register(...); no edits to the
supervisor or peers.

Handoffs are explicit and typed (see schemas Handoff). Every handoff appends an
event to state.tool_events so the mission-control UI can draw the arrow with its
reason.

## Supervisor / Orchestrator

- Purpose: understand intent, keep the plan of work, route to the right specialist,
  decide when the turn is done.
- Input: full TravelState (messages, trip_brief, itinerary, options, pending
  bookings, errors).
- Output: sets state.next_agent (one of the registered agents, or "done").
- Decision rules: assembled at runtime from the registry descriptions plus state
  signals - is there a trip_brief yet, are there pending approvals, did an agent
  report an error and ask to re-route.
- Delegates: to any specialist; ends the turn when the user's need is met.

## Trip Planning Agent

- Purpose: turn preferences, budget, duration, and style into a personalized,
  feasible itinerary.
- Input: trip_brief, retrieved destination knowledge, long-term preferences.
- Output: state.itinerary = structured plan (days -> items with geo, timing, cost
  estimate).
- Tools: geocoding (to anchor the destination), plus knowledge retrieval.
- Delegates: to Destination Intelligence for facts/weather/POIs, to Logistics for
  timing feasibility, to Booking for availability and pricing.

## Destination Intelligence Agent

- Purpose: real-time and reference info - attractions, weather, local recs,
  advisories.
- Input: destination name or geo, dates.
- Output: writes facts into state.context (weather summary, POI candidates,
  destination overview); can trigger proactive re-planning when conditions change.
- Tools: Open-Meteo (weather), OpenTripMap / Overpass (POIs), Nominatim
  (geocoding), Wikivoyage/Wikipedia (content), REST Countries; RAG over the
  knowledge base.
- Delegates: feeds the planner; publishes weather_changed events for re-planning.

## Logistics Coordinator Agent (Phase 2)

- Purpose: schedules, transport timing, buffers, day-of sequencing; validates the
  plan is physically doable (travel times between stops).
- Input: state.itinerary.
- Output: annotated itinerary with timing and buffers, or a list of fixes.
- Delegates: back to the planner with fixes when timing does not work.

## Personalization / Memory Agent (Phase 2, supporting)

- Purpose: read and write long-term memory; inject relevant preferences into
  planning; summarize the session into durable facts at the end.
- Input: user_id, session messages.
- Output: memory writes to the store (namespaced per user_id); preference hints
  into state.context.

## Booking Agent (Phase 3)

- Purpose: search and price flights, hotels, activities across providers; confirm
  only after explicit user approval.
- Input: itinerary items, traveler details.
- Output: state.options -> state.pending_bookings -> state.confirmed_bookings
  (only after the interrupt clears).
- Rules: never confirm without the human-in-the-loop approval gate; idempotency
  keys on every book call; re-confirm availability against planner constraints.

## Traveler Support Agent (Phase 3)

- Purpose: 24/7 support - cancellations, modifications, emergency info, questions.
- Rules: changes that touch bookings coordinate with the Booking Agent and route
  irreversible actions through the same approval gate.

## Shared state contract

See apps/api/odyssey/graph/state.py for TravelState. Key fields: messages
(add_messages reducer), user_id, session_id, active_agent, next_agent, trip_brief,
itinerary, options, pending_bookings, confirmed_bookings, context, tool_events
(append-only, powers mission-control), errors (append-only degradation log).
