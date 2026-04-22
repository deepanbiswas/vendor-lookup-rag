"""Lightweight HTTP checks for Ollama and Qdrant (Streamlit sidebar / startup)."""

from __future__ import annotations

import httpx

from vendor_lookup_rag.config import Settings


def fetch_services_health(
    settings: Settings,
    *,
    timeout_s: float = 2.0,
) -> dict[str, tuple[bool, str]]:
    """Return ``{service: (ok, detail)}`` using URLs from settings."""
    return fetch_services_health_urls(settings.ollama_base_url, settings.qdrant_url, timeout_s=timeout_s)


def fetch_services_health_urls(
    ollama_base_url: str,
    qdrant_url: str,
    *,
    timeout_s: float = 2.0,
) -> dict[str, tuple[bool, str]]:
    """
    Return ``{service: (ok, detail)}`` for Ollama and Qdrant.

    Detail is a short human-readable status (error text or ``ok``).
    """
    out: dict[str, tuple[bool, str]] = {}
    out["ollama"] = _check_ollama(ollama_base_url, timeout_s)
    out["qdrant"] = _check_qdrant(qdrant_url, timeout_s)
    return out


def _check_ollama(base_url: str, timeout_s: float) -> tuple[bool, str]:
    url = base_url.rstrip("/") + "/api/tags"
    try:
        r = httpx.get(url, timeout=timeout_s)
        r.raise_for_status()
        return True, "reachable"
    except Exception as e:
        return False, str(e)[:200]


def _check_qdrant(base_url: str, timeout_s: float) -> tuple[bool, str]:
    url = base_url.rstrip("/") + "/readyz"
    try:
        r = httpx.get(url, timeout=timeout_s)
        if r.status_code == 200:
            return True, "ready"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)[:200]
