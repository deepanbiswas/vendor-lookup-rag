#!/usr/bin/env bash
# Fail fast if Qdrant / Ollama are not reachable (same endpoints as health/http.py).
# Usage:
#   ./scripts/verify_stack.sh              # Qdrant /readyz + Ollama /api/tags
#   ./scripts/verify_stack.sh qdrant-only # only Qdrant (matches CI integration job scope)
# Env (optional; defaults match .env.example and tests/conftest.py):
#   QDRANT_URL          default http://localhost:6333
#   OLLAMA_BASE_URL     default http://localhost:11434
#   VERIFY_STACK_QDRANT_ONLY=1  same as qdrant-only

set -euo pipefail

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

qdrant_only=false
if [[ "${1:-}" == "qdrant-only" ]] || [[ "${VERIFY_STACK_QDRANT_ONLY:-}" == "1" ]]; then
  qdrant_only=true
fi

qdrant_readyz="${QDRANT_URL%/}/readyz"
echo "Checking Qdrant: GET ${qdrant_readyz}"
if ! curl -sfS --max-time 5 "${qdrant_readyz}" >/dev/null; then
  echo "FAIL: Qdrant not ready. Start with: docker compose up -d (repo root)" >&2
  exit 1
fi
echo "OK: Qdrant ready"

if [[ "${qdrant_only}" == true ]]; then
  exit 0
fi

ollama_tags="${OLLAMA_BASE_URL%/}/api/tags"
echo "Checking Ollama: GET ${ollama_tags}"
if ! curl -sfS --max-time 5 "${ollama_tags}" >/dev/null; then
  echo "FAIL: Ollama not reachable. Install from https://ollama.com and start the daemon." >&2
  exit 1
fi
echo "OK: Ollama reachable"
