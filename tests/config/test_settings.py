"""Tests for application settings."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from vendor_lookup_rag.config import Settings, get_column_mapping, get_settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.qdrant_url == "http://localhost:6333"
    assert s.qdrant_collection == "vendor_master"
    assert s.embedding_model == "nomic-embed-text"
    assert s.chat_model == "gemma4:e4b"
    assert s.embedding_vector_size == 768
    assert s.retrieval_top_k == 5
    assert s.ingest_upsert_batch_size == 128
    assert s.vector_backend == "qdrant"
    assert s.embedding_backend == "ollama"
    assert s.agent_backend == "pydantic_ai"
    assert s.app_log_dir is None
    assert s.app_log_level == "ERROR"
    assert s.retrieval_min_score is None
    assert s.telemetry_log_dir is None
    assert s.telemetry_log_to_stderr is False
    assert s.telemetry_log_to_stdout is False


def test_ollama_openai_api_base() -> None:
    s = Settings(ollama_base_url="http://host:11434")
    assert s.ollama_openai_api_base() == "http://host:11434/v1"
    t = Settings(ollama_base_url="http://host:11434/v1")
    assert t.ollama_openai_api_base() == "http://host:11434/v1"


def test_settings_strips_trailing_slash_on_urls() -> None:
    s = Settings(ollama_base_url="http://localhost:11434/", qdrant_url="http://qdrant:6333/")
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.qdrant_url == "http://qdrant:6333"


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("QDRANT_COLLECTION", "vendors_test")
    monkeypatch.setenv("EMBEDDING_MODEL", "mxbai-embed-large")
    monkeypatch.setenv("EMBEDDING_VECTOR_SIZE", "1024")
    get_settings.cache_clear()
    s = get_settings()
    assert s.ollama_base_url == "http://ollama:11434"
    assert s.qdrant_url == "http://qdrant:6333"
    assert s.qdrant_collection == "vendors_test"
    assert s.embedding_model == "mxbai-embed-large"
    assert s.embedding_vector_size == 1024


def test_ingest_upsert_batch_size_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("INGEST_UPSERT_BATCH_SIZE", "32")
    get_settings.cache_clear()
    s = get_settings()
    assert s.ingest_upsert_batch_size == 32
    get_settings.cache_clear()


def test_invalid_threshold_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCORE_THRESHOLD_EXACT", "2.0")
    with pytest.raises(ValidationError):
        Settings()


def test_get_column_mapping_from_env_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mp = tmp_path / "map.json"
    mp.write_text(
        json.dumps({"legal_name": ["custom_legal"]}),
        encoding="utf-8",
    )
    get_settings.cache_clear()
    monkeypatch.setenv("VENDOR_CSV_COLUMN_MAP_PATH", str(mp))
    get_settings.cache_clear()
    m = get_column_mapping()
    assert m.legal_name == ["custom_legal"]
    assert "vendor_id" in m.vendor_id
    get_settings.cache_clear()
