"""Smoke tests: package import and version (TDD baseline)."""

import pytest

from vendor_lookup_rag import __version__


@pytest.mark.spec("specs/vendor-lookup-agent-specifications.md#s4-version-discoverability")
def test_package_has_version() -> None:
    assert isinstance(__version__, str)
    parts = __version__.split(".")
    assert len(parts) >= 2
