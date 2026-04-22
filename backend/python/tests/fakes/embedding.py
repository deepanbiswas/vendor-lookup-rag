"""In-memory :class:`~vendor_lookup_rag.ports.embedding.TextEmbedder` for tests."""

from __future__ import annotations

from collections.abc import Callable


class FakeTextEmbedder:
    def __init__(
        self,
        vector: list[float] | None = None,
        *,
        embed_fn: Callable[[str], list[float]] | None = None,
        side_effect: BaseException | None = None,
    ) -> None:
        self._vector = list(vector) if vector is not None else [1.0]
        self._embed_fn = embed_fn
        self._side_effect = side_effect
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        if self._side_effect is not None:
            raise self._side_effect
        if self._embed_fn is not None:
            return self._embed_fn(text)
        return list(self._vector)
