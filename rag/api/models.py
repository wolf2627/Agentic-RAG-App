"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field, validator


class SourceAttribution(BaseModel):
    """Source attribution for an answer."""
    chunk_id: str
    document: str
    score: float


class AskRequest(BaseModel):
    """Request payload for /ask (question must be non-empty and reasonably sized)."""
    question: str = Field(..., min_length=3, max_length=500, description="Natural language question to answer")

    @validator("question", pre=True)
    def strip_and_validate(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("question must be a string")
        q = v.strip()
        if not q:
            raise ValueError("question must not be empty or whitespace")
        if len(q) < 3:
            raise ValueError("question too short after trimming")
        return q


class AskResponse(BaseModel):
    """Response payload for /ask."""
    answer: str
    sources: list[SourceAttribution]
