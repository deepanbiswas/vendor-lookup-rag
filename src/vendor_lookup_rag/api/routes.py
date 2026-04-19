"""REST routes for chat and status."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from vendor_lookup_rag.agent.run_trace import format_agent_run_trace
from vendor_lookup_rag.api.schemas import ChatRequest, ChatResponse, HealthResponse, ServiceHealth, StatusResponse
from vendor_lookup_rag.api.runtime import AppRuntime
from vendor_lookup_rag.health import fetch_services_health_urls
from vendor_lookup_rag.ui.chat_display import assistant_markdown_from_run

_logger = logging.getLogger(__name__)

router = APIRouter()


def get_runtime(request: Request) -> AppRuntime:
    rt = getattr(request.app.state, "runtime", None)
    if rt is None:
        raise HTTPException(status_code=503, detail="API runtime not initialized")
    return rt


@router.get(
    "/v1/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Service health",
    description="Reports whether Ollama and Qdrant respond to HTTP health checks.",
)
def get_health(runtime: Annotated[AppRuntime, Depends(get_runtime)]) -> HealthResponse:
    s = runtime.settings
    raw = fetch_services_health_urls(s.ollama_base_url, s.qdrant_url)
    services = {name: ServiceHealth(ok=ok, detail=detail) for name, (ok, detail) in raw.items()}
    return HealthResponse(services=services)


@router.get(
    "/v1/status",
    response_model=StatusResponse,
    tags=["status"],
    summary="Status and configuration",
    description="Same dependency health as `/v1/health`, plus chat/embedding model names and score thresholds.",
)
def get_status(runtime: Annotated[AppRuntime, Depends(get_runtime)]) -> StatusResponse:
    s = runtime.settings
    raw = fetch_services_health_urls(s.ollama_base_url, s.qdrant_url)
    services = {name: ServiceHealth(ok=ok, detail=detail) for name, (ok, detail) in raw.items()}
    return StatusResponse(
        services=services,
        chat_model=s.chat_model,
        embedding_model=s.embedding_model,
        score_threshold_exact=s.score_threshold_exact,
        score_threshold_partial=s.score_threshold_partial,
        score_tolerance=s.score_tolerance,
    )


@router.post(
    "/v1/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Chat turn",
    description="Runs the vendor lookup agent once and returns rendered markdown plus a trace string.",
)
def post_chat(
    body: ChatRequest,
    runtime: Annotated[AppRuntime, Depends(get_runtime)],
) -> ChatResponse:
    try:
        result = runtime.agent.run_sync(body.message, deps=runtime.deps)
        display = assistant_markdown_from_run(result)
        trace_text = format_agent_run_trace(result)
        _logger.info("Chat turn completed (display length=%s chars).", len(display))
        return ChatResponse(display_markdown=display, trace_text=trace_text)
    except Exception as e:
        _logger.exception("Agent run failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail=str(e),
        ) from e
