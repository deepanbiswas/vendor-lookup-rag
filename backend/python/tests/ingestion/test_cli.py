"""Tests for vendor-ingest CLI."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import vendor_lookup_rag.ingestion.cli as ingest_cli


def test_cli_success_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["vendor-ingest", "any.csv"])
    with patch.object(ingest_cli, "ingest_vendor_csv", return_value=3):
        with pytest.raises(SystemExit) as exc:
            ingest_cli.main()
    assert exc.value.code == 0


def test_cli_failure_exits_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["vendor-ingest", "any.csv"])
    with patch.object(ingest_cli, "ingest_vendor_csv", side_effect=RuntimeError("boom")):
        with pytest.raises(SystemExit) as exc:
            ingest_cli.main()
    assert exc.value.code == 1


def test_cli_dry_run_exits_zero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    p = tmp_path / "rows.csv"
    p.write_text("vendor_id,legal_name\nv1,Acme\nv2,Beta\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["vendor-ingest", "--dry-run", str(p)])
    with pytest.raises(SystemExit) as exc:
        ingest_cli.main()
    assert exc.value.code == 0


def test_cli_dry_run_skips_ingest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    p = tmp_path / "rows.csv"
    p.write_text("vendor_id,legal_name\nv1,Acme\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["vendor-ingest", "--dry-run", str(p)])
    with patch.object(ingest_cli, "ingest_vendor_csv") as mock_ingest:
        with pytest.raises(SystemExit) as exc:
            ingest_cli.main()
    assert exc.value.code == 0
    mock_ingest.assert_not_called()
