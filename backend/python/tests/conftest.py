"""Shared pytest fixtures for vendor_lookup_rag."""

import os

import httpx
import pytest


def _qdrant_reachable(url: str) -> bool:
    try:
        r = httpx.get(f"{url.rstrip('/')}/collections", timeout=2.0)
        return r.status_code < 500
    except (httpx.HTTPError, OSError):
        return False


def _ollama_reachable(url: str) -> bool:
    try:
        r = httpx.get(f"{url.rstrip('/')}/api/tags", timeout=2.0)
        return r.status_code < 500
    except (httpx.HTTPError, OSError):
        return False


@pytest.fixture
def qdrant_url() -> str:
    return os.environ.get("QDRANT_URL", "http://localhost:6333")


@pytest.fixture
def skip_if_no_qdrant(qdrant_url: str) -> None:
    if not _qdrant_reachable(qdrant_url):
        pytest.skip("Qdrant not reachable; start with: docker compose up -d")


@pytest.fixture
def skip_if_no_ollama() -> None:
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    if not _ollama_reachable(base):
        pytest.skip("Ollama not reachable; install from ollama.com and start the daemon")
