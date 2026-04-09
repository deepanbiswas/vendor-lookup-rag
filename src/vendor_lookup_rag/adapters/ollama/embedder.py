"""Ollama :class:`~vendor_lookup_rag.ports.embedding.TextEmbedder` implementation (HTTP)."""

from __future__ import annotations

import logging

import httpx

_logger = logging.getLogger(__name__)


def _embedding_from_embed_response(data: object) -> list[float]:
    """Parse ``/api/embed`` JSON (``embeddings`` list of vectors)."""
    if not isinstance(data, dict):
        raise ValueError(f"Ollama /api/embed: expected JSON object, got {type(data).__name__}")
    raw = data.get("embeddings")
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"Ollama /api/embed response missing non-empty 'embeddings': {data!r}")
    first = raw[0]
    if not isinstance(first, list) or not first:
        raise ValueError(f"Ollama /api/embed: first embedding missing or empty: {data!r}")
    try:
        return [float(x) for x in first]
    except (TypeError, ValueError) as e:
        raise ValueError(f"Ollama /api/embed: invalid embedding values: {data!r}") from e


def _embedding_from_embeddings_response(data: object) -> list[float]:
    """Parse legacy ``/api/embeddings`` JSON (single ``embedding`` vector)."""
    if not isinstance(data, dict):
        raise ValueError(f"Ollama /api/embeddings: expected JSON object, got {type(data).__name__}")
    emb = data.get("embedding")
    if not isinstance(emb, list) or not emb:
        raise ValueError(f"Ollama /api/embeddings response missing 'embedding': {data!r}")
    try:
        return [float(x) for x in emb]
    except (TypeError, ValueError) as e:
        raise ValueError(f"Ollama /api/embeddings: invalid embedding values: {data!r}") from e


class OllamaEmbedder:
    """
    Sync client for Ollama embedding HTTP APIs.

    Tries **POST /api/embed** first (current Ollama; response shape ``embeddings``).
    Falls back to **POST /api/embeddings** on **404** (older daemons).
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        client: httpx.Client | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._model = model
        self._own_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def _post_json(self, path: str, body: dict) -> httpx.Response:
        return self._client.post(f"{self._base}{path}", json=body)

    def _raise_http(self, exc: httpx.HTTPStatusError) -> None:
        r = exc.response
        snippet = (r.text or "")[:300].strip()
        detail = f" {snippet!r}" if snippet else ""
        msg = (
            f"Ollama embedding request failed: HTTP {r.status_code} at {r.request.url!r}.{detail} "
            f"If the model is missing, run: ollama pull {self._model}"
        )
        _logger.error("%s", msg)
        raise RuntimeError(msg) from exc

    def embed(self, text: str) -> list[float]:
        """Return embedding vector for a single string."""
        t = (text or "").strip()
        if not t:
            raise ValueError("embed() requires non-empty text after stripping whitespace.")

        payload = {"model": self._model, "input": t}

        try:
            r = self._post_json("/api/embed", payload)
            if r.status_code == 404:
                _logger.warning(
                    "Ollama returned 404 for /api/embed; falling back to /api/embeddings (model=%s).",
                    self._model,
                )
                r2 = self._post_json("/api/embeddings", payload)
                try:
                    r2.raise_for_status()
                except httpx.HTTPStatusError as e:
                    self._raise_http(e)
                return _embedding_from_embeddings_response(r2.json())

            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                self._raise_http(e)
            return _embedding_from_embed_response(r.json())
        except httpx.RequestError as e:
            _logger.error("Cannot reach Ollama at %s: %s", self._base, e)
            raise RuntimeError(
                f"Cannot reach Ollama at {self._base!r} ({e}). "
                "Is the daemon running? See https://ollama.com"
            ) from e

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> OllamaEmbedder:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
