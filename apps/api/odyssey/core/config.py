"""Central configuration. Reads .env (repo root) and process env.

One Settings object, cached. Two run modes are expressed here:
  - stack: Postgres checkpointer/store, Qdrant vectors, Redis, Langfuse.
  - local: SQLite checkpointer, in-process store, Chroma (or none), no Docker.

Agents never read env directly; they read this Settings object via get_settings().
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root is three parents up from this file: odyssey/core/config.py -> api -> repo.
_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", "apps/api/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Run mode ----
    mode: Literal["stack", "local"] = Field(default="local", alias="ODYSSEY_MODE")
    env: str = Field(default="dev", alias="ODYSSEY_ENV")
    log_level: str = Field(default="INFO", alias="ODYSSEY_LOG_LEVEL")
    log_json: bool = Field(default=True, alias="ODYSSEY_LOG_JSON")

    # ---- LLM ----
    llm_provider: Literal["groq", "ollama", "openai"] = Field(
        default="groq", alias="ODYSSEY_LLM_PROVIDER"
    )
    llm_model: str = Field(default="llama-3.3-70b-versatile", alias="ODYSSEY_LLM_MODEL")
    llm_temperature: float = Field(default=0.3, alias="ODYSSEY_LLM_TEMPERATURE")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL")

    # ---- Persistence ----
    database_url: str = Field(
        default="postgresql+psycopg://odyssey:odyssey@localhost:5432/odyssey",
        alias="DATABASE_URL",
    )
    sqlite_path: str = Field(default="./data/odyssey.sqlite", alias="SQLITE_PATH")
    checkpoint_sqlite_path: str = Field(
        default="./data/checkpoints.sqlite", alias="CHECKPOINT_SQLITE_PATH"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # ---- Vectors ----
    vector_backend: Literal["qdrant", "chroma", "none"] = Field(
        default="chroma", alias="VECTOR_BACKEND"
    )
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="odyssey_knowledge", alias="QDRANT_COLLECTION")
    chroma_path: str = Field(default="./data/chroma", alias="CHROMA_PATH")
    embed_model: str = Field(default="BAAI/bge-small-en-v1.5", alias="EMBED_MODEL")

    # ---- Tool keys (optional; tools degrade gracefully) ----
    opentripmap_api_key: str = Field(default="", alias="OPENTRIPMAP_API_KEY")
    nominatim_user_agent: str = Field(
        default="odyssey-dev (contact: dev@example.com)", alias="NOMINATIM_USER_AGENT"
    )

    # ---- Observability ----
    langfuse_enabled: bool = Field(default=False, alias="LANGFUSE_ENABLED")
    langfuse_host: str = Field(default="http://localhost:3001", alias="LANGFUSE_HOST")
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")

    # ---- Auth / security ----
    jwt_secret: str = Field(
        default="change-me-in-production-please-32-chars-min", alias="JWT_SECRET"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_ttl_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_TTL_MINUTES")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    # ---- CORS ----
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # ---- Derived helpers ----
    @property
    def is_local(self) -> bool:
        return self.mode == "local"

    @property
    def repo_root(self) -> Path:
        return _REPO_ROOT

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def resolve_path(self, rel: str) -> Path:
        """Resolve a possibly-relative data path against the repo root."""
        p = Path(rel)
        return p if p.is_absolute() else (self.repo_root / p)

    @property
    def llm_configured(self) -> bool:
        if self.llm_provider == "groq":
            return bool(self.groq_api_key)
        if self.llm_provider == "openai":
            return bool(self.openai_api_key and self.openai_base_url)
        return True  # ollama needs no key


@lru_cache
def get_settings() -> Settings:
    return Settings()
