"""LLM provider abstraction.

Every LLM in Odyssey is obtained here. Switching provider is one env var
(ODYSSEY_LLM_PROVIDER). All providers return a LangChain BaseChatModel so tool
binding, structured output, streaming, and astream_events behave identically.

  groq   -> ChatGroq (default; strong open-weights tool calling on a free tier)
  ollama -> ChatOllama (local open weights)
  openai -> ChatOpenAI with a custom base_url (vLLM / TGI / OpenRouter / Together)
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel

from odyssey.core.config import Settings, get_settings
from odyssey.core.logging import get_logger

log = get_logger(__name__)


class LLMNotConfiguredError(RuntimeError):
    """Raised when the selected provider is missing required credentials."""


def build_chat_model(
    settings: Settings | None = None,
    *,
    temperature: float | None = None,
    model: str | None = None,
) -> BaseChatModel:
    """Construct a chat model for the configured provider."""
    s = settings or get_settings()
    provider = s.llm_provider
    temp = s.llm_temperature if temperature is None else temperature
    model_name = model or s.llm_model

    if provider == "groq":
        if not s.groq_api_key:
            raise LLMNotConfiguredError(
                "ODYSSEY_LLM_PROVIDER=groq but GROQ_API_KEY is empty. "
                "Get a free key at https://console.groq.com/keys and set it in .env."
            )
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model_name,
            temperature=temp,
            api_key=s.groq_api_key,
            max_retries=2,
        )

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as e:  # optional extra
            raise LLMNotConfiguredError(
                "ollama provider selected but langchain-ollama is not installed. "
                'Install the extra: pip install -e ".[llm]"'
            ) from e
        return ChatOllama(
            model=model_name,
            temperature=temp,
            base_url=s.ollama_base_url,
        )

    if provider == "openai":
        if not (s.openai_api_key and s.openai_base_url):
            raise LLMNotConfiguredError(
                "openai provider selected but OPENAI_API_KEY / OPENAI_BASE_URL are unset."
            )
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:  # optional extra
            raise LLMNotConfiguredError(
                "openai provider selected but langchain-openai is not installed. "
                'Install the extra: pip install -e ".[llm]"'
            ) from e
        return ChatOpenAI(
            model=model_name,
            temperature=temp,
            api_key=s.openai_api_key,
            base_url=s.openai_base_url,
            max_retries=2,
        )

    raise LLMNotConfiguredError(f"Unknown LLM provider: {provider!r}")


@lru_cache
def get_chat_model() -> BaseChatModel:
    """Cached default chat model for the process."""
    s = get_settings()
    log.info("llm.init", provider=s.llm_provider, model=s.llm_model)
    return build_chat_model(s)


def llm_health() -> dict:
    """Lightweight readiness signal without making a network call."""
    s = get_settings()
    return {
        "provider": s.llm_provider,
        "model": s.llm_model,
        "configured": s.llm_configured,
    }
