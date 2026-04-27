#!/usr/bin/env bash
# Fail fast if Qdrant / Ollama (and optionally the vendor HTTP API) are not reachable.
# Same Qdrant/Ollama endpoints as backend/python/src/health/http.py.
#
# Usage:
#   ./scripts/verify_stack.sh                 # Qdrant /readyz + Ollama /api/tags
#   ./scripts/verify_stack.sh qdrant-only     # only Qdrant (matches CI integration job scope)
#   ./scripts/verify_stack.sh with-api        # Qdrant + Ollama + vendor API GET /v1/health
#
# Env (optional; defaults match .env.example and tests/conftest.py):
#   QDRANT_URL                    default http://localhost:6333
#   OLLAMA_BASE_URL               default http://localhost:11434
#   VENDOR_LOOKUP_API_BASE_URL    default http://127.0.0.1:8000 (used with with-api only)
#   VERIFY_STACK_QDRANT_ONLY=1    same as qdrant-only
#   VERIFY_STACK_WITH_API=1       same as passing with-api (ignored if qdrant-only)

set -euo pipefail

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
VENDOR_LOOKUP_API_BASE_URL="${VENDOR_LOOKUP_API_BASE_URL:-http://127.0.0.1:8000}"

qdrant_only=false
with_api=false
for arg in "$@"; do
  case "$arg" in
    qdrant-only) qdrant_only=true ;;
    with-api) with_api=true ;;
  esac
done

if [[ "${VERIFY_STACK_QDRANT_ONLY:-}" == "1" ]]; then
  qdrant_only=true
fi
if [[ "${VERIFY_STACK_WITH_API:-}" == "1" ]]; then
  with_api=true
fi

if [[ "${qdrant_only}" == true ]]; then
  with_api=false
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

if [[ "${with_api}" == true ]]; then
  api_health="${VENDOR_LOOKUP_API_BASE_URL%/}/v1/health"
  echo "Checking vendor API: GET ${api_health}"
  if ! curl -sfS --max-time 5 "${api_health}" >/dev/null; then
    echo "FAIL: Vendor API not reachable at ${VENDOR_LOOKUP_API_BASE_URL}. Start with: vendor-api (or python -m vendor_lookup_rag.api)" >&2
    exit 1
  fi
  echo "OK: Vendor API reachable"
fi
