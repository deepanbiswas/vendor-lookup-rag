"""Tests for Ollama/Qdrant HTTP health helpers."""

from __future__ import annotations

import httpx
import pytest
import respx

from vendor_lookup_rag.health import fetch_services_health_urls


@respx.mock
def test_fetch_services_health_urls_both_ok() -> None:
    respx.get("http://ollama:11434/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
    respx.get("http://qdrant:6333/readyz").mock(return_value=httpx.Response(200, json={}))
    out = fetch_services_health_urls("http://ollama:11434", "http://qdrant:6333")
    assert out["ollama"][0] is True
    assert out["qdrant"][0] is True


@respx.mock
def test_fetch_services_health_urls_ollama_fails() -> None:
    respx.get("http://localhost:11434/api/tags").mock(side_effect=httpx.ConnectError("refused"))
    respx.get("http://localhost:6333/readyz").mock(return_value=httpx.Response(200))
    out = fetch_services_health_urls("http://localhost:11434", "http://localhost:6333")
    assert out["ollama"][0] is False
    assert "refused" in out["ollama"][1] or "refused" in str(out["ollama"][1])


@respx.mock
def test_fetch_services_health_urls_qdrant_non_200() -> None:
    respx.get("http://localhost:11434/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
    respx.get("http://localhost:6333/readyz").mock(return_value=httpx.Response(503))
    out = fetch_services_health_urls("http://localhost:11434", "http://localhost:6333")
    assert out["qdrant"][0] is False
    assert "503" in out["qdrant"][1]
