# Odyssey API image. Used by docker compose (ODYSSEY_MODE=stack).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# System deps for psycopg + build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY odyssey ./odyssey
RUN pip install --upgrade pip && pip install -e ".[stack,local,llm,auth]"

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "odyssey.main:app", "--host", "0.0.0.0", "--port", "8000"]
