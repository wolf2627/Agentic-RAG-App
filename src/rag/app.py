"""FastAPI application entry point for the question-answering microservice.

This module initializes the FastAPI app, registers exception handlers,
and configures all API routes.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from tenacity import RetryError

from src.rag.api.error_handlers import (
    validation_exception_handler,
    http_exception_handler,
    retry_exception_handler,
    generic_exception_handler,
)
from src.rag.api.models import AskResponse
from src.rag.api.routes import qa

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(title="Question Answering Service", version="1.0.0")

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RetryError, retry_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register routes
app.add_api_route("/ask", qa.ask_question, methods=["POST"], response_model=AskResponse)
app.add_api_route("/health", qa.health_check, methods=["GET"], status_code=status.HTTP_200_OK)
app.add_api_route("/", qa.root, methods=["GET"], response_class=JSONResponse)