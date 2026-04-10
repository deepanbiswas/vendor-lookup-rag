# Local / team dev stack runbook

Single path to bring up dependencies, align environment variables with CI, and verify health before long test or ingest runs.

## 1. One command path (Qdrant + host Ollama)

**Qdrant (Docker):** from the repository root:

```bash
docker compose up -d
```

This uses `docker-compose.yml` (pinned Qdrant image ≥ 1.16). HTTP is on port **6333**.

**Ollama (host):** install from [ollama.com](https://ollama.com) and keep the default listen address so **`OLLAMA_BASE_URL=http://localhost:11434`** matches `.env.example`. Pull the models referenced in `.env` (tags must appear in `ollama list`):

```bash
ollama pull nomic-embed-text    # EMBEDDING_MODEL
ollama pull gemma4:e4b          # CHAT_MODEL (or your chosen CHAT_MODEL tag)
```

**App config:** copy env defaults and adjust if needed:

```bash
cp .env.example .env
```

## 2. Health checks

Runtime checks in code use [`src/vendor_lookup_rag/health/http.py`](../src/vendor_lookup_rag/health/http.py): Qdrant **`GET …/readyz`**, Ollama **`GET …/api/tags`**.

Before integration tests or heavy jobs, run the shell helper (same endpoints):

```bash
./scripts/verify_stack.sh
```

Qdrant-only (same surface area as the **integration Qdrant** CI job, which does not require Ollama):

```bash
./scripts/verify_stack.sh qdrant-only
# or: VERIFY_STACK_QDRANT_ONLY=1 ./scripts/verify_stack.sh
```

Override URLs if your `.env` differs:

```bash
QDRANT_URL=http://127.0.0.1:6333 OLLAMA_BASE_URL=http://localhost:11434 ./scripts/verify_stack.sh
```

## 3. Environment for integration runs

Use the same variable names **locally and in CI** so pytest invocations match.

| Variable | Role | Typical local value | CI (Qdrant job) |
|----------|------|---------------------|-----------------|
| `QDRANT_URL` | HTTP API base for Qdrant | `http://localhost:6333` | `http://127.0.0.1:6333` |
| `OLLAMA_BASE_URL` | Ollama HTTP API | `http://localhost:11434` | *(not set in Qdrant-only job)* |

`tests/conftest.py` defaults match `.env.example` when variables are unset.

**Integration (Qdrant, no live Ollama)** — align with [`.github/workflows/vendor-lookup-rag-ci.yml`](../.github/workflows/vendor-lookup-rag-ci.yml):

```bash
export QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}"
./scripts/verify_stack.sh qdrant-only
pytest -m "integration and not requires_ollama" --tb=short -v
```

**Integration including Ollama** (after `./scripts/verify_stack.sh`):

```bash
export QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
pytest -m "requires_ollama" --tb=short -v   # scope as needed; see README “Tests”
```

Using `http://127.0.0.1:6333` vs `http://localhost:6333` is interchangeable for a local Qdrant container; CI sets `127.0.0.1` explicitly.
