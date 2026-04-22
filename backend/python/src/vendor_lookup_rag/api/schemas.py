"""REST request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ServiceHealth(BaseModel):
    ok: bool
    detail: str


class HealthResponse(BaseModel):
    """Ollama and Qdrant reachability only (``fetch_services_health_urls``)."""

    services: dict[str, ServiceHealth]


class StatusResponse(BaseModel):
    """Sidebar: service reachability plus model/threshold hints from server settings."""

    services: dict[str, ServiceHealth]
    chat_model: str
    embedding_model: str
    score_threshold_exact: float
    score_threshold_partial: float
    score_tolerance: float


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)

    @field_validator("message")
    @classmethod
    def strip_nonempty(cls, v: str) -> str:
        t = v.strip()
        if not t:
            raise ValueError("message must not be empty")
        return t


class ChatResponse(BaseModel):
    display_markdown: str
    trace_text: str
