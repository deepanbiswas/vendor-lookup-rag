"""Streamlit chat UI for vendor lookup."""

from __future__ import annotations

import hashlib
import json
import logging

import streamlit as st

from vendor_lookup_rag.agent import AgentDeps
from vendor_lookup_rag.agent.run_trace import format_agent_run_trace
from vendor_lookup_rag.adapters.factory import make_text_embedder, make_vendor_agent_runner, open_vector_store
from vendor_lookup_rag.config import Settings, get_settings
from vendor_lookup_rag.health import fetch_services_health_urls
from vendor_lookup_rag.observability import configure_app_logging, configure_observability
from vendor_lookup_rag.ui.chat_display import assistant_markdown_from_run as _assistant_markdown_from_run

# Cap session history to avoid unbounded memory on long sessions.
MAX_CHAT_MESSAGES = 128

_logger = logging.getLogger(__name__)


def _settings_cache_signature(s: Settings) -> str:
    """Stable hash so ``st.cache_resource`` rebuilds when ``.env`` / env vars change."""
    payload = json.dumps(s.model_dump(), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


@st.cache_resource
def _deps(settings_sig: str) -> AgentDeps:
    get_settings.cache_clear()
    s = get_settings()
    # Avoid startup warning when Qdrant is unreachable; health is shown in the sidebar.
    handle = open_vector_store(s, check_compatibility=False)
    emb = make_text_embedder(s)
    return AgentDeps(settings=s, embedder=emb, store=handle.store)


@st.cache_data(ttl=15)
def _cached_services_health(ollama_base_url: str, qdrant_url: str) -> dict[str, tuple[bool, str]]:
    return fetch_services_health_urls(ollama_base_url, qdrant_url)


def _trim_messages(messages: list[dict]) -> None:
    while len(messages) > MAX_CHAT_MESSAGES:
        messages.pop(0)


def main() -> None:
    get_settings.cache_clear()
    s_boot = get_settings()
    configure_app_logging(s_boot)
    st.set_page_config(page_title="Vendor Lookup", page_icon="🔎")
    st.title("Vendor Lookup Agent")
    st.caption("Local RAG against your vendor master (Ollama + Qdrant).")

    deps = _deps(_settings_cache_signature(s_boot))
    configure_observability(deps.settings)
    agent = make_vendor_agent_runner(deps.settings)
    s = deps.settings

    if "messages" not in st.session_state:
        st.session_state.messages = []

    pending = st.session_state.get("pending_agent_prompt")
    agent_busy = pending is not None
    show_trace = bool(st.session_state.get("show_agent_trace", False))

    with st.sidebar:
        st.subheader("Connection")
        health = _cached_services_health(s.ollama_base_url, s.qdrant_url)
        for name, (ok, detail) in health.items():
            icon = "🟢" if ok else "🔴"
            st.markdown(f"{icon} **{name}:** `{detail}`")
        st.caption("Checks refresh every ~15s (cached).")

        st.subheader("Models")
        st.code(f"chat: {s.chat_model}\nembed: {s.embedding_model}", language="text")
        st.caption(
            f"Match thresholds (from env): exact ≥ {s.score_threshold_exact}, "
            f"partial ≥ {s.score_threshold_partial}, tolerance ±{s.score_tolerance}"
        )

        st.subheader("Observability")
        st.caption(
            "OpenTelemetry / Logfire traces are exported to your configured backends "
            "(not rendered here). The toggle below shows the **agent run transcript** "
            "(full top‑k retrieval, usage, messages) under replies."
        )
        st.checkbox(
            "Show agent run details under replies",
            key="show_agent_trace",
            disabled=agent_busy,
            help="Hidden while a search is running so toggling does not interrupt the run.",
        )

        if st.button("Clear chat", type="secondary"):
            st.session_state.messages = []
            st.session_state.pop("pending_agent_prompt", None)
            st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if (
                show_trace
                and m["role"] == "assistant"
                and m.get("trace")
            ):
                with st.expander("Agent run details (transcript & usage)", expanded=False):
                    st.code(m["trace"], language="json")

    if pending is not None:
        with st.spinner("Thinking…"):
            try:
                result = agent.run_sync(pending, deps=deps)
                display = _assistant_markdown_from_run(result)
                trace_text = format_agent_run_trace(result)
                _logger.info("Agent completed a chat turn (display length=%s chars).", len(display))
            except Exception as e:
                st.error(
                    "**Something went wrong calling the agent.** "
                    "Check that Ollama is running, the chat model is pulled, and Qdrant is reachable "
                    f"({s.qdrant_url}).\n\n`{e}`"
                )
                st.session_state.pop("pending_agent_prompt", None)
                st.stop()
        st.session_state.messages.append(
            {"role": "assistant", "content": display, "trace": trace_text},
        )
        _trim_messages(st.session_state.messages)
        st.session_state.pop("pending_agent_prompt", None)
        st.rerun()

    if prompt := st.chat_input("Describe the vendor (name, VAT, city, …)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        _trim_messages(st.session_state.messages)
        st.session_state.pending_agent_prompt = prompt
        st.rerun()


if __name__ == "__main__":
    main()
