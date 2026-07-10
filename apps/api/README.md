# Odyssey API

FastAPI backend for Odyssey - the LangGraph multi-agent travel platform core.

See the repo root `README.md` for the full architecture and run instructions, and
`../../AGENTS.md` for the agent contracts.

## Quick start (local mode, no Docker)

```bash
python -m venv .venv
. .venv/Scripts/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev,local,llm]"
cp ../../.env.example ../../.env   # then set GROQ_API_KEY
ODYSSEY_MODE=local uvicorn odyssey.main:app --reload --port 8000
```

Health: http://localhost:8000/health  Readiness: http://localhost:8000/ready
Metrics: http://localhost:8000/metrics  Docs: http://localhost:8000/docs

## Layout

- `odyssey/core` - config, logging, telemetry, observability, guardrails, security
- `odyssey/providers` - LLM provider abstraction + external tool clients + mock booking providers
- `odyssey/graph` - TravelState, agent registry, graph assembly, checkpointer/store, streaming
- `odyssey/agents` - one module per agent (supervisor + specialists)
- `odyssey/knowledge` - vector store repository (Qdrant/Chroma) + retrieval
- `odyssey/memory` - long-term semantic memory
- `odyssey/api` - FastAPI routers
- `odyssey/schemas` - Pydantic contracts
- `odyssey/db` - SQLAlchemy models + Alembic
