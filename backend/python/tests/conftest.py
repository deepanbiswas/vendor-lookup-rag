"""Shared pytest fixtures for vendor_lookup_rag."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

# Allow `pytest` without a prior `pip install -e .` (code lives in `../src/`, import name is `vendor_lookup_rag`).
try:
    import vendor_lookup_rag  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - local dev only
    _init = Path(__file__).resolve().parent.parent / "src" / "__init__.py"
    if _init.is_file():
        _spec = importlib.util.spec_from_file_location(
            "vendor_lookup_rag",
            _init,
            submodule_search_locations=[str(_init.parent)],
        )
        if _spec and _spec.loader:
            _m = importlib.util.module_from_spec(_spec)
            sys.modules["vendor_lookup_rag"] = _m
            _spec.loader.exec_module(_m)
    else:  # pragma: no cover
        raise

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
