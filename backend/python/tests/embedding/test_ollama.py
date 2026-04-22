"""Tests for Ollama embedding client."""

import httpx
import pytest
import respx

from vendor_lookup_rag.embedding import OllamaEmbedder


@respx.mock
def test_embed_parses_api_embed_response() -> None:
    respx.post("http://ollama:11434/api/embed").mock(
        return_value=httpx.Response(
            200,
            json={"embeddings": [[0.1, 0.2, 0.3]]},
        )
    )
    emb = OllamaEmbedder("http://ollama:11434", "nomic-embed-text")
    try:
        v = emb.embed("hello")
        assert v == [0.1, 0.2, 0.3]
    finally:
        emb.close()


@respx.mock
def test_embed_falls_back_to_api_embeddings_on_404() -> None:
    respx.post("http://ollama:11434/api/embed").mock(return_value=httpx.Response(404))
    respx.post("http://ollama:11434/api/embeddings").mock(
        return_value=httpx.Response(
            200,
            json={"embedding": [0.4, 0.5]},
        )
    )
    emb = OllamaEmbedder("http://ollama:11434", "nomic-embed-text")
    try:
        assert emb.embed("hello") == [0.4, 0.5]
    finally:
        emb.close()


@respx.mock
def test_embed_raises_runtime_error_on_http_error() -> None:
    respx.post("http://ollama:11434/api/embed").mock(return_value=httpx.Response(500, text="err"))
    emb = OllamaEmbedder("http://ollama:11434", "nomic-embed-text")
    try:
        with pytest.raises(RuntimeError, match="Ollama embedding request failed"):
            emb.embed("x")
    finally:
        emb.close()


def test_embed_rejects_empty_text() -> None:
    with httpx.Client() as c:
        emb = OllamaEmbedder("http://ollama:11434", "nomic-embed-text", client=c)
        with pytest.raises(ValueError, match="non-empty"):
            emb.embed("")
        with pytest.raises(ValueError, match="non-empty"):
            emb.embed("   ")


@pytest.mark.requires_ollama
@pytest.mark.integration
def test_embed_real_ollama_if_available(skip_if_no_ollama: None) -> None:
    """Optional: run with Ollama up and embedding model pulled."""
    from vendor_lookup_rag.config import get_settings

    s = get_settings()
    emb = OllamaEmbedder(s.ollama_base_url, s.embedding_model)
    try:
        v = emb.embed("test")
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        pytest.skip(f"Embedding call failed (model missing or API error): {e}")
    finally:
        emb.close()
    assert len(v) == s.embedding_vector_size
