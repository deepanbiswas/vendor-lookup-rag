# Python FastAPI (`vendor-api`) and ingest tools; dependencies from backend/python only.
# Streamlit UI: use Dockerfile.streamlit. C# API: see backend/csharp/Dockerfile.
# Python 3.12 matches requires-python >=3.11
FROM python:3.12-slim-bookworm

WORKDIR /app

COPY backend/python/pyproject.toml backend/python/README.md /app/backend/python/
COPY backend/python/src /app/backend/python/src

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e /app/backend/python

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["vendor-api"]
