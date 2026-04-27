"""Build production :class:`~vendor_lookup_rag.api.runtime.AppRuntime`."""

from __future__ import annotations

import logging

from vendor_lookup_rag.adapters.factory import (
    make_text_embedder,
    make_vendor_agent_runner,
    open_vector_store,
)
from vendor_lookup_rag.agent.deps import AgentDeps
from vendor_lookup_rag.config import Settings, get_settings
from vendor_lookup_rag.observability import configure_app_logging, configure_observability
from vendor_lookup_rag.api.runtime import AppRuntime

_logger = logging.getLogger(__name__)


def build_production_runtime() -> AppRuntime:
    """Open vector store + embedder, wire agent (same as former Streamlit ``_deps`` + runner)."""
    get_settings.cache_clear()
    s = get_settings()
    configure_app_logging(s)
    configure_observability(s)
    handle = open_vector_store(s, check_compatibility=False)
    emb = make_text_embedder(s)
    deps = AgentDeps(settings=s, embedder=emb, store=handle.store)
    agent = make_vendor_agent_runner(s)
    _logger.info("API runtime ready (collection=%s)", s.qdrant_collection)
    return AppRuntime(agent=agent, deps=deps, settings=s, vector_handle=handle)
