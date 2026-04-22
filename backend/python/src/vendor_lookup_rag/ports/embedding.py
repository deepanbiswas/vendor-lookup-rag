"""Embedding provider port."""

from __future__ import annotations

from typing import Protocol


class TextEmbedder(Protocol):
    """Maps text to a dense embedding vector."""

    def embed(self, text: str) -> list[float]: ...
