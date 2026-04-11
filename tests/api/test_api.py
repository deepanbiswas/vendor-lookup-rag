"""API route tests with injected runtime (no Ollama/Qdrant)."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from tests.fakes import FakeAgentRunResult, FakeAgentUsage, FakeVendorAgentRunner
from vendor_lookup_rag.agent.deps import AgentDeps
from vendor_lookup_rag.api.main import create_app
from vendor_lookup_rag.api.runtime import AppRuntime
from vendor_lookup_rag.config import Settings


def _fake_settings() -> Settings:
    return Settings(agent_instrument=False)


def _minimal_runtime(agent: FakeVendorAgentRunner) -> AppRuntime:
    mock_deps = MagicMock(spec=AgentDeps)
    mock_deps.settings = _fake_settings()
    mock_embedder = MagicMock()
    mock_embedder.close = MagicMock()
    mock_deps.embedder = mock_embedder
    return AppRuntime(agent=agent, deps=mock_deps, settings=mock_deps.settings)


def test_get_health_returns_services_only() -> None:
    agent = FakeVendorAgentRunner()
    rt = _minimal_runtime(agent)
    app = create_app(runtime=rt)
    with TestClient(app) as client:
        r = client.get("/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"services"}
    assert "ollama" in data["services"]
    assert "qdrant" in data["services"]


def test_get_status_returns_services_and_config() -> None:
    agent = FakeVendorAgentRunner()
    rt = _minimal_runtime(agent)
    app = create_app(runtime=rt)
    with TestClient(app) as client:
        r = client.get("/v1/status")
    assert r.status_code == 200
    data = r.json()
    assert "services" in data
    assert "ollama" in data["services"]
    assert "qdrant" in data["services"]
    assert "chat_model" in data
    assert "embedding_model" in data
    assert "score_threshold_exact" in data


def test_post_chat_returns_display_and_trace() -> None:
    result = FakeAgentRunResult(
        output="OK",
        run_id="run-1",
        usage_obj=FakeAgentUsage(input_tokens=1, output_tokens=2, total_tokens=3),
        messages_json=b"[]",
    )
    agent = FakeVendorAgentRunner(result)
    rt = _minimal_runtime(agent)
    app = create_app(runtime=rt)
    with TestClient(app) as client:
        r = client.post("/v1/chat", json={"message": "Acme Corp"})
    assert r.status_code == 200
    data = r.json()
    assert "display_markdown" in data
    assert "trace_text" in data
    assert "run-1" in data["trace_text"]
    assert agent.run_sync_calls and agent.run_sync_calls[0][0] == "Acme Corp"


def test_post_chat_validation_empty_message() -> None:
    agent = FakeVendorAgentRunner()
    rt = _minimal_runtime(agent)
    app = create_app(runtime=rt)
    with TestClient(app) as client:
        r = client.post("/v1/chat", json={"message": "   "})
    assert r.status_code == 422
