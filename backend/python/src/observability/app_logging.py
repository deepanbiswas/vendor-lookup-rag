"""Application logging: stdout always; optional rotating file under :attr:`Settings.app_log_dir`."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from vendor_lookup_rag.config import Settings, get_settings

_LOG_ROOT_NAME = "vendor_lookup_rag"
_LOG_FILE = "vendor_lookup_rag.log"
_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 5

_LEVEL_NAMES: dict[str, int] = {
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _numeric_level(name: str) -> int:
    u = name.strip().upper()
    if u == "WARN":
        u = "WARNING"
    if u not in _LEVEL_NAMES:
        raise ValueError(f"Invalid log level {name!r}; use ERROR, WARNING, INFO, or DEBUG.")
    return _LEVEL_NAMES[u]


def configure_app_logging(settings: Settings | None = None) -> None:
    """
    Configure the ``vendor_lookup_rag`` logger: one stdout handler (always) and optionally
    a rotating file under :attr:`Settings.app_log_dir`.

    Safe to call multiple times (e.g. Streamlit reruns): handlers are replaced so duplicates
    are not accumulated. Effective level is :attr:`Settings.app_log_level` (default ``ERROR``).
    """
    s = settings or get_settings()
    level = _numeric_level(s.app_log_level)
    log = logging.getLogger(_LOG_ROOT_NAME)
    log.handlers.clear()
    log.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(level)
    stdout.setFormatter(fmt)
    log.addHandler(stdout)

    if s.app_log_dir:
        base = Path(s.app_log_dir)
        base.mkdir(parents=True, exist_ok=True)
        path = base / _LOG_FILE
        fh = RotatingFileHandler(
            path,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        fh.setLevel(level)
        fh.setFormatter(fmt)
        log.addHandler(fh)

    log.propagate = False
