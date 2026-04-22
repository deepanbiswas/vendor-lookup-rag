"""Streamlit AppTest smoke tests (mocked API client)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from vendor_lookup_streamlit.settings import StreamlitSettings

import vendor_lookup_streamlit.app as app_module
_APP_PY = (
    Path(__file__).resolve().parents[4]
    / "frontend"
    / "streamlit"
    / "src"
    / "vendor_lookup_streamlit"
    / "app.py"
)


@pytest.fixture(autouse=True)
def _clear_streamlit_caches() -> None:
    app_module._cached_api_status.clear()
    yield


def test_format_agent_run_trace_includes_usage() -> None:
    from tests.fakes import FakeAgentRunResult, FakeAgentUsage
    from vendor_lookup_rag.agent.run_trace import format_agent_run_trace

    result = FakeAgentRunResult(
        output="x",
        run_id="rid-1",
        usage_obj=FakeAgentUsage(input_tokens=3, output_tokens=7, total_tokens=10),
        messages_json=b'[{"role":"assistant"}]',
    )
    text = format_agent_run_trace(result)
    assert "rid-1" in text
    assert "input_tokens=3" in text
    assert "assistant" in text


def test_streamlit_main_renders_title_with_mocks() -> None:
    fake_status = {
        "services": {
            "ollama": {"ok": True, "detail": "reachable"},
            "qdrant": {"ok": True, "detail": "ready"},
        },
        "chat_model": "gemma4:e4b",
        "embedding_model": "nomic-embed-text",
        "score_threshold_exact": 0.92,
        "score_threshold_partial": 0.55,
        "score_tolerance": 0.0,
    }

    def get_settings_patched() -> StreamlitSettings:
        return StreamlitSettings(vendor_lookup_api_base_url="http://127.0.0.1:8000")

    get_settings_patched.cache_clear = lambda: None  # type: ignore[attr-defined, misc]

    with (
        patch.object(app_module, "_cached_api_status", return_value=fake_status),
        patch.object(app_module, "get_settings", get_settings_patched),
    ):
        at = AppTest.from_file(_APP_PY)
        at.run(timeout=10)

    titles = [t.value for t in at.title]
    assert any("Vendor Lookup Agent" in (v or "") for v in titles)
