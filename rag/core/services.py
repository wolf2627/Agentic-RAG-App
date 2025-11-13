"""Business logic services for retrieval and answer generation."""

from __future__ import annotations

import asyncio
import logging

from fastapi import HTTPException, status
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, RetryError

from rag.api.models import SourceAttribution
from rag.config import Settings
from rag.openai_client import OpenAIClient
from rag.vector_store import VectorStore, RetrievedChunk

logger = logging.getLogger(__name__)

# Retry/backoff configuration
_MAX_RETRIES = 5
_WAIT = wait_exponential(multiplier=1, min=1, max=30)  # exponential backoff with cap


def _should_retry(exc: Exception) -> bool:
    """Return True if exception appears transient (429 or 5xx-like or network timeouts)."""
    # If the exception has an HTTP-like status attribute
    status_attr = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    try:
        if status_attr is not None:
            code = int(status_attr)
            if code == 429 or 500 <= code < 600:
                return True
    except Exception:
        # ignore conversion errors and fall back to message-based checks
        pass

    msg = str(exc).lower()
    if "rate limit" in msg or "too many requests" in msg or "429" in msg:
        return True
    if "server error" in msg or "internal" in msg or "temporar" in msg:
        return True

    # Common transient network errors - treat as retryable
    if isinstance(exc, TimeoutError):
        return True

    return False


# Synchronous wrappers with tenacity (called from threads)
@retry(
    reraise=True,
    stop=stop_after_attempt(_MAX_RETRIES),
    wait=_WAIT,
    retry=retry_if_exception(_should_retry),
)
def _retrieve_context_sync(vector_store: VectorStore, question: str, client: OpenAIClient, top_k: int):
    """Synchronous retrieval call wrapped with retries. Intended to be run in a thread."""
    return vector_store.similarity_search_text(question, client=client, top_k=top_k)


@retry(
    reraise=True,
    stop=stop_after_attempt(_MAX_RETRIES),
    wait=_WAIT,
    retry=retry_if_exception(_should_retry),
)
def _generate_answer_sync(openai_client: OpenAIClient, instructions: str, prompt: str, model: str, max_output_tokens: int, temperature: float):
    """Synchronous generation call wrapped with retries. Intended to be run in a thread."""
    return openai_client.generate_answer(
        instructions=instructions,
        prompt=prompt,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )


# Async helpers calling the sync wrappers via threads
async def retrieve_context(*, question: str, openai_client: OpenAIClient, vector_store: VectorStore, top_k: int) -> list[RetrievedChunk]:
    """Retrieve relevant document chunks for the question (with retries for transient failures)."""
    try:
        chunks = await asyncio.to_thread(_retrieve_context_sync, vector_store, question, openai_client, top_k)
        return chunks
    except RetryError as re:
        logger.error("Retries exhausted during retrieval: %s", re)
        # Do not expose internal exception text to the client
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Context retrieval failed after retries")
    except Exception as e:
        logger.exception("Error during context retrieval")
        # Sanitize for client
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Context retrieval failed") from e


async def generate_answer(*, question: str, chunks: list[RetrievedChunk], openai_client: OpenAIClient, settings: Settings) -> str:
    """Generate an answer given the question and retrieved chunks (with retries for transient failures)."""
    if not chunks:
        context_prompt = "No context passages were retrieved. Answer conservatively."
    else:
        formatted_chunks = []
        for chunk in chunks:
            document = str(
                chunk.metadata.get("source_path")
                or chunk.metadata.get("document_id")
                or chunk.chunk_id,
            )
            formatted_chunks.append(
                f"{chunk.chunk_id} ({document}):\n{chunk.content.strip()}"
            )
        context_prompt = "\n\n".join(formatted_chunks)

    prompt = (
        "Context passages:\n"
        f"{context_prompt}\n\n"
        f"Question: {question}\n"
        "Respond with a factual answer that cites chunk identifiers in parentheses."
    )

    try:
        answer_text = await asyncio.to_thread(
            _generate_answer_sync,
            openai_client,
            settings.response_instructions,
            prompt,
            settings.response_model,
            settings.response_max_tokens,
            settings.response_temperature,
        )
        if not answer_text:
            raise RuntimeError("Empty response from OpenAI")
        return answer_text.strip()
    except RetryError as re:
        logger.error("Retries exhausted during generation: %s", re)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Generation failed after retries")
    except HTTPException:
        # propagate HTTPException unchanged
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Generation failed")
        # Sanitize for client
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Generation failed") from exc


def sources_from_chunks(chunks: list[RetrievedChunk]) -> list[SourceAttribution]:
    """Convert retrieved chunks to source attributions."""
    sources: list[SourceAttribution] = []
    for chunk in chunks:
        document = str(
            chunk.metadata.get("source_path")
            or chunk.metadata.get("document_id")
            or chunk.chunk_id,
        )
        sources.append(
            SourceAttribution(
                chunk_id=chunk.chunk_id,
                document=document,
                score=float(chunk.score),
            )
        )
    return sources
