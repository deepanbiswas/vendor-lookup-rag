"""Run with: ``python -m vendor_lookup_rag.api`` or ``vendor-api``."""

from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    host = os.environ.get("VENDOR_LOOKUP_API_HOST", "127.0.0.1")
    port = int(os.environ.get("VENDOR_LOOKUP_API_PORT", "8000"))
    uvicorn.run(
        "vendor_lookup_rag.api.main:app",
        host=host,
        port=port,
        factory=False,
    )


if __name__ == "__main__":
    main()
