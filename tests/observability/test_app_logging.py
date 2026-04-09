"""Tests for application logging setup."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from vendor_lookup_rag.config import Settings
from vendor_lookup_rag.observability.app_logging import configure_app_logging


def test_configure_app_logging_stdout_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    s = Settings(app_log_dir=None, app_log_level="INFO")
    configure_app_logging(s)
    log = logging.getLogger("vendor_lookup_rag")
    assert log.level == logging.INFO
    assert len(log.handlers) == 1
    assert isinstance(log.handlers[0], logging.StreamHandler)


def test_configure_app_logging_with_file_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    log_dir = tmp_path / "logs"
    s = Settings(app_log_dir=str(log_dir), app_log_level="WARNING")
    configure_app_logging(s)
    log = logging.getLogger("vendor_lookup_rag")
    assert log.level == logging.WARNING
    assert len(log.handlers) == 2
    assert (log_dir / "vendor_lookup_rag.log").is_file() or True  # created on first emit
    log.warning("test message")
    assert (log_dir / "vendor_lookup_rag.log").is_file()


def test_settings_warn_normalizes_to_warning() -> None:
    s = Settings.model_validate({"app_log_level": "warn"})
    assert s.app_log_level == "WARNING"
