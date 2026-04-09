"""Compatibility entry: re-exports the Streamlit UI from :mod:`vendor_lookup_rag.ui.app`."""

from vendor_lookup_rag.ui import app as _ui_app

main = _ui_app.main
_deps = _ui_app._deps
_cached_services_health = _ui_app._cached_services_health

__all__ = ["main", "_deps", "_cached_services_health"]

if __name__ == "__main__":
    main()
