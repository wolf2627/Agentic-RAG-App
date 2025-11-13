"""Centralized exception handlers and error response utilities."""

import json
import logging
import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from tenacity import RetryError

logger = logging.getLogger(__name__)


def _json_safe(value: object) -> object:
    """Convert value to JSON-safe representation."""
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, (set, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _error_payload(status_code: int, message: str, *, details: object | None = None) -> dict[str, object]:
    """Create standardized error payload."""
    error: dict[str, object] = {
        "status": int(status_code),
        "message": str(message),
    }
    if details is not None:
        error["details"] = _json_safe(details)
    return {"error": error}


def _error_response(status_code: int, message: str, *, details: object | None = None) -> JSONResponse:
    """Create standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content=_error_payload(status_code, message, details=details),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.info("Validation error for %s %s: %s", request.method, request.url, exc.errors())
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation failed",
        details=exc.errors(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    detail = exc.detail
    if isinstance(detail, str) and detail.strip():
        message = detail.strip()
        details = None
    else:
        message = "Request failed"
        details = detail
    logger.info(
        "HTTP exception %s for %s %s: %s",
        exc.status_code,
        request.method,
        request.url,
        {"message": message, "details": details},
    )
    return _error_response(status_code=exc.status_code, message=message, details=details)


async def retry_exception_handler(request: Request, exc: RetryError):
    """Handle retry exhaustion errors."""
    logger.error("Retries exhausted for request %s %s: %s", request.method, request.url, traceback.format_exc())
    return _error_response(
        status_code=status.HTTP_502_BAD_GATEWAY,
        message="Upstream service temporarily unavailable; please retry later.",
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.exception("Unhandled exception handling request %s %s: %s", request.method, request.url, traceback.format_exc())
    return _error_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Internal server error")
