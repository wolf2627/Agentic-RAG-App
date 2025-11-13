"""API endpoints for the question-answering service."""

from __future__ import annotations

import logging
from typing import AsyncIterator

from fastapi import Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse

from rag.api.dependencies import get_settings_dep, get_vector_store_dep, get_openai_client_dep
from rag.api.error_handlers import _error_payload
from rag.api.models import AskRequest, AskResponse
from rag.api.utils import serialize_event
from rag.config import Settings
from rag.core.services import retrieve_context, generate_answer, sources_from_chunks
from rag.openai_client import OpenAIClient
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


async def ask_question(
    body: AskRequest,
    stream: bool = Query(False, description="Stream chunked progress events"),
    settings: Settings = Depends(get_settings_dep),
    vector_store: VectorStore = Depends(get_vector_store_dep),
    openai_client: OpenAIClient = Depends(get_openai_client_dep),
):
    """
    POST /ask - Answer a question using RAG.
    
    Retrieves relevant context from the vector store and generates an answer
    using OpenAI's API.
    """
    logger.info("Received question request: %s", body.question)

    # Retrieve context with retries handled in the wrapper
    chunks = await retrieve_context(
        question=body.question,
        vector_store=vector_store,
        openai_client=openai_client,
        top_k=settings.top_k,
    )

    if not stream:
        answer_text = await generate_answer(
            question=body.question,
            chunks=chunks,
            openai_client=openai_client,
            settings=settings,
        )
        response = AskResponse(answer=answer_text, sources=sources_from_chunks(chunks))
        return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())

    async def event_stream() -> AsyncIterator[bytes]:
        sources = sources_from_chunks(chunks)
        yield serialize_event(
            "context",
            {
                "question": body.question,
                "sources": [source.model_dump() for source in sources],
            },
        )

        try:
            answer_text = await generate_answer(
                question=body.question,
                chunks=chunks,
                openai_client=openai_client,
                settings=settings,
            )
            yield serialize_event(
                "answer",
                {
                    "answer": answer_text,
                    "sources": [source.model_dump() for source in sources],
                },
            )
        except HTTPException as exc:
            # exc.detail may be structured (dict/list) thanks to our handlers
            status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
            detail_payload = exc.detail

            if (
                isinstance(detail_payload, dict)
                and isinstance(detail_payload.get("error"), dict)
                and detail_payload["error"].get("message")
            ):
                error_block = detail_payload["error"]
                message = str(error_block.get("message", "Request failed"))
                details = error_block.get("details")
            elif isinstance(detail_payload, str) and detail_payload.strip():
                message = detail_payload.strip()
                details = None
            else:
                message = "Request failed"
                details = detail_payload

            yield serialize_event(
                "error",
                _error_payload(
                    status_code,
                    message,
                    details=details,
                ),
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Streaming error")
            yield serialize_event(
                "error",
                _error_payload(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Internal streaming error",
                ),
            )

    return StreamingResponse(event_stream(), media_type="application/json")


async def health_check() -> JSONResponse:
    """GET /health - Health check endpoint."""
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)


async def root() -> JSONResponse:
    """GET / - Simple root endpoint with service info."""
    info = {
        "service": "Question Answering Service",
        "version": "1.0.0",
        "endpoints": {
            "/ask": "POST endpoint to ask a question",
            "/health": "GET health check endpoint",
        },
    }
    return JSONResponse(content=info, status_code=status.HTTP_200_OK)
