"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI

from vendor_lookup_rag.api.deps import build_production_runtime
from vendor_lookup_rag.api.routes import router
from vendor_lookup_rag.api.runtime import AppRuntime


def create_app(*, runtime: AppRuntime | None = None) -> FastAPI:
    """
    Create the REST API app.

    Pass ``runtime`` for tests; otherwise the lifespan builds production runtime (Ollama + Qdrant).
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if runtime is not None:
            app.state.runtime = runtime
        else:
            app.state.runtime = build_production_runtime()
        try:
            yield
        finally:
            rt: AppRuntime = app.state.runtime
            rt.shutdown()

    app = FastAPI(
        title="Vendor Lookup API",
        version="0.1.0",
        description=(
            "Vendor lookup over a vector index with a conversational agent. "
            "OpenAPI 3.x document is served at `/openapi.json` and browsable via Swagger UI at `/docs`."
        ),
        openapi_tags=[
            {"name": "health", "description": "Reachability of Ollama and Qdrant."},
            {"name": "status", "description": "Health plus model and scoring settings exposed to clients."},
            {"name": "chat", "description": "Run one agent turn with vendor retrieval."},
        ],
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
