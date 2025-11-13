"""Dependency injection factories for FastAPI endpoints."""

from functools import lru_cache

from fastapi import Depends

from src.rag.config import Settings, get_settings
from src.rag.openai_client import OpenAIClient, OpenAIClientConfig
from src.rag.vector_store import get_vector_store, VectorStore


@lru_cache(maxsize=1)
def _get_vector_store_cached(settings: Settings) -> VectorStore:
    """Cached factory for VectorStore singleton."""
    return get_vector_store(settings)


@lru_cache(maxsize=1)
def _get_openai_client_cached(settings: Settings) -> OpenAIClient:
    """Cached factory for OpenAIClient singleton."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    config = OpenAIClientConfig(
        api_key=settings.openai_api_key,
        embed_model=settings.embed_model,
        timeout=settings.openai_timeout,
        max_retries=settings.max_embed_retries,
    )
    return OpenAIClient(config)


def get_settings_dep() -> Settings:
    """Dependency for injecting Settings."""
    return get_settings()


def get_vector_store_dep(settings: Settings = Depends(get_settings_dep)) -> VectorStore:
    """Dependency for injecting VectorStore."""
    return _get_vector_store_cached(settings)


def get_openai_client_dep(settings: Settings = Depends(get_settings_dep)) -> OpenAIClient:
    """Dependency for injecting OpenAIClient."""
    return _get_openai_client_cached(settings)
