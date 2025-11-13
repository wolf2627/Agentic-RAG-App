"""API package containing models, dependencies, and error handlers."""

from rag.api.models import AskRequest, AskResponse, SourceAttribution
from rag.api.dependencies import get_settings_dep, get_vector_store_dep, get_openai_client_dep

__all__ = [
    "AskRequest",
    "AskResponse",
    "SourceAttribution",
    "get_settings_dep",
    "get_vector_store_dep",
    "get_openai_client_dep",
]
