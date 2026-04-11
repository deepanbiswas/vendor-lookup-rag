# Vendor Lookup RAG — one image, multiple entrypoints:
#   Default CMD: Streamlit UI (:8501).
#   Override CMD: `vendor-api` for the FastAPI vendor lookup API (:8000). See docker-compose.yml (services `app` vs `api`).
#   CLI: `vendor-ingest` for CSV → Qdrant (unchanged).
# Python 3.12 matches requires-python >=3.11
FROM python:3.12-slim-bookworm

WORKDIR /app

# Minimal build deps for any wheels; keep image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000
EXPOSE 8501

# Default: Streamlit UI. Override with e.g. `vendor-api` for the REST API service (see docker-compose.yml).
CMD ["streamlit", "run", "src/vendor_lookup_rag/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
