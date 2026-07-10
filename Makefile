# Odyssey task runner. On Windows without `make`, run the underlying commands
# shown here directly, or use Git Bash which includes make.

API := apps/api
WEB := apps/web

.PHONY: help
help:
	@echo "Odyssey targets:"
	@echo "  make up          - docker compose up (full stack: pg, redis, qdrant, langfuse, api, web)"
	@echo "  make down        - docker compose down"
	@echo "  make dev-api     - run the API locally (ODYSSEY_MODE=local, no Docker)"
	@echo "  make dev-web     - run the Next.js frontend locally"
	@echo "  make install     - install api (venv) and web (npm) deps"
	@echo "  make migrate     - run alembic migrations"
	@echo "  make seed        - seed OpenFlights + knowledge base"
	@echo "  make test        - run backend + frontend tests"
	@echo "  make lint        - ruff + type check + eslint"
	@echo "  make eval        - run the eval harness"

.PHONY: up
up:
	docker compose up --build

.PHONY: down
down:
	docker compose down

.PHONY: install
install:
	cd $(API) && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd $(WEB) && npm install

.PHONY: dev-api
dev-api:
	cd $(API) && . .venv/bin/activate && ODYSSEY_MODE=local uvicorn odyssey.main:app --reload --port 8000

.PHONY: dev-web
dev-web:
	cd $(WEB) && npm run dev

.PHONY: migrate
migrate:
	cd $(API) && . .venv/bin/activate && alembic upgrade head

.PHONY: seed
seed:
	cd $(API) && . .venv/bin/activate && python -m odyssey.db.seed

.PHONY: test
test:
	cd $(API) && . .venv/bin/activate && pytest -q
	cd $(WEB) && npm test --silent

.PHONY: lint
lint:
	cd $(API) && . .venv/bin/activate && ruff check . && pyright
	cd $(WEB) && npm run lint

.PHONY: eval
eval:
	cd $(API) && . .venv/bin/activate && python -m odyssey.evals.run
