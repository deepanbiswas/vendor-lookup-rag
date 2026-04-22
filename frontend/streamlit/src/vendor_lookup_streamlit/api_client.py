"""HTTP client for the vendor lookup REST API (Streamlit UI)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

_logger = logging.getLogger(__name__)


def _base(base_url: str) -> str:
    return base_url.rstrip("/")


def fetch_status(base_url: str, *, timeout_s: float = 5.0) -> dict[str, Any]:
    """GET /v1/status — sidebar health + model/threshold hints."""
    url = f"{_base(base_url)}/v1/status"
    with httpx.Client(timeout=timeout_s) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.json()


def post_chat(base_url: str, message: str, *, timeout_s: float = 120.0) -> tuple[str, str]:
    """
    POST /v1/chat — returns (display_markdown, trace_text).
    """
    url = f"{_base(base_url)}/v1/chat"
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, json={"message": message})
        r.raise_for_status()
        data = r.json()
        return str(data["display_markdown"]), str(data["trace_text"])
