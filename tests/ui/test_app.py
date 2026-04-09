"""Streamlit AppTest smoke tests (mocked agent/deps)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest

import vendor_lookup_rag.ui.app as app_module
from tests.fakes import FakeAgentRunResult, FakeAgentUsage, FakeVendorAgentRunner
from vendor_lookup_rag.config import Settings

_APP_PY = Path(__file__).resolve().parents[2] / "src" / "vendor_lookup_rag" / "ui" / "app.py"


@pytest.fixture(autouse=True)
def _clear_streamlit_caches() -> None:
    app_module._deps.clear()
    app_module._cached_services_health.clear()
    yield


def test_format_agent_run_trace_includes_usage() -> None:
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
    mock_deps = MagicMock()
    mock_deps.settings = Settings(agent_instrument=False)
    mock_agent = FakeVendorAgentRunner(
        FakeAgentRunResult(
            output="Here is the answer.",
            run_id="run-x",
            usage_obj=FakeAgentUsage(input_tokens=1, output_tokens=2, total_tokens=3),
            messages_json=b"[]",
        ),
    )

    with (
        patch.object(app_module, "_deps", return_value=mock_deps),
        patch.object(app_module, "make_vendor_agent_runner", return_value=mock_agent),
        patch.object(app_module, "configure_observability"),
        patch.object(
            app_module,
            "_cached_services_health",
            return_value={"ollama": (True, "reachable"), "qdrant": (True, "ready")},
        ),
    ):
        at = AppTest.from_file(_APP_PY)
        at.run(timeout=10)

    titles = [t.value for t in at.title]
    assert any("Vendor Lookup Agent" in (v or "") for v in titles)
