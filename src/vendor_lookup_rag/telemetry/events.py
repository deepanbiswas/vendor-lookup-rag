"""Structured telemetry for retrieval (JSON lines).

Writes one JSON object per line. Destinations are controlled via :class:`Settings`:

* Optional directory: ``vendor_retrieval.jsonl`` and ``vendor_agent_tool.jsonl`` under
  :attr:`Settings.telemetry_log_dir`
* Optional :attr:`Settings.telemetry_log_to_stderr` / :attr:`Settings.telemetry_log_to_stdout`

Agent runs also emit OpenTelemetry spans when :attr:`Settings.agent_instrument` is true;
export with standard ``OTEL_*`` env vars. Optional Logfire: :func:`vendor_lookup_rag.observability.logfire.configure_observability`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from threading import Lock

from vendor_lookup_rag.config import Settings

_write_lock = Lock()


def telemetry_enabled(settings: Settings) -> bool:
    return bool(
        settings.telemetry_log_dir
        or settings.telemetry_log_to_stderr
        or settings.telemetry_log_to_stdout,
    )


def _emit_jsonl(settings: Settings, payload: dict, filename: str) -> None:
    if not telemetry_enabled(settings):
        return
    line = json.dumps(payload, ensure_ascii=False, default=str) + "\n"
    if settings.telemetry_log_to_stderr:
        sys.stderr.write(line)
    if settings.telemetry_log_to_stdout:
        sys.stdout.write(line)
    if settings.telemetry_log_dir:
        base = Path(settings.telemetry_log_dir)
        base.mkdir(parents=True, exist_ok=True)
        log_path = base / filename
        with _write_lock:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(line)


def emit_agent_tool_event(settings: Settings, payload: dict) -> None:
    """Structured line for agent tool runs (same destinations as retrieval when enabled)."""
    _emit_jsonl(settings, {"event": "vendor_agent_tool", **payload}, "vendor_agent_tool.jsonl")


def emit_retrieval_event(settings: Settings, payload: dict) -> None:
    """Append one JSON line per event when at least one telemetry destination is enabled."""
    _emit_jsonl(settings, payload, "vendor_retrieval.jsonl")
