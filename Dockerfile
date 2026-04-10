# Vendor Lookup RAG — Streamlit UI + ingestion CLI (vendor-ingest)
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

EXPOSE 8501

# Bind on all interfaces so Docker port mapping works
CMD ["streamlit", "run", "src/vendor_lookup_rag/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
