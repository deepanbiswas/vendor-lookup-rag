"""Compatibility entry: re-exports the Streamlit UI from :mod:`vendor_lookup_rag.ui.app`."""

from vendor_lookup_rag.ui import app as _ui_app

main = _ui_app.main
_cached_api_status = _ui_app._cached_api_status

__all__ = ["main", "_cached_api_status"]

if __name__ == "__main__":
    main()
