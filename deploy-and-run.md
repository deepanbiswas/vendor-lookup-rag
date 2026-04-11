# Deploy and run (macOS and Windows)

This project runs **Qdrant**, the **FastAPI vendor API**, and the **Streamlit** UI in **Docker**. **Ollama** runs on the host machine and is installed with the scripts in `scripts/` (platform-specific). For local development run order, health scripts, and integration-test environment variables (parity with CI), see the **[README.md](README.md)** “Local stack” and “Health checks and integration test env” sections.

| Component       | How it runs                                                                                   |
| --------------- | --------------------------------------------------------------------------------------------- |
| Qdrant          | Docker (`docker-compose.yml` → service `qdrant`)                                              |
| Vendor REST API | Docker (`docker-compose.yml` → service `api`, port **8000**, command `vendor-api`)            |
| Streamlit app   | Docker (`docker-compose.yml` → service `app`, port **8501**)                                  |
| Ollama          | Host — install with `scripts/install-ollama-macos.sh` or `scripts/install-ollama-windows.ps1` |


The Compose file sets `QDRANT_URL` and `OLLAMA_BASE_URL` on the **`api`** service so the API talks to Qdrant on the Docker network and Ollama on your machine. The **`app`** (Streamlit) service sets `VENDOR_LOOKUP_API_BASE_URL=http://api:8000` so the UI only calls the REST API.

---

## Prerequisites (both platforms)

1. **Docker Desktop** (or another Docker engine with Compose V2): [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. **Git** (to clone the repo).
3. This repository checked out locally.

---

## macOS

### 1. Install Ollama (script)

From the repository root:

```bash
chmod +x scripts/install-ollama-macos.sh
./scripts/install-ollama-macos.sh
```

This uses **Homebrew** to install Ollama, starts the service, and pulls `nomic-embed-text` and `gemma4:e4b` (see `.env.example`).

If you do not use Homebrew, install Ollama from [ollama.com](https://ollama.com) and run the same `ollama pull` commands manually.

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if needed (models, thresholds). For **Docker Compose**, you normally **do not** need to change `QDRANT_URL` or `OLLAMA_BASE_URL` in `.env` — `docker-compose.yml` overrides them for the **`api`** service. The Streamlit service does not require those variables at runtime (it uses `VENDOR_LOOKUP_API_BASE_URL` from Compose).

### 3. Start Qdrant, API, and Streamlit

From the repository root:

```bash
docker compose up --build -d
```

- Qdrant HTTP API: `http://localhost:6333`
- Vendor REST API: `http://localhost:8000` (OpenAPI docs: `/docs`)
- Streamlit UI: `http://localhost:8501`

### 4. Ingest vendor CSV (one-off)

Mount your CSV into the container and run `vendor-ingest` (paths below assume `data/vendor-data.csv` on the host):

```bash
docker compose run --rm \
  -v "$(pwd)/data:/data:ro" \
  app vendor-ingest /data/vendor-data.csv
```

Use `--dry-run` first if you only want to validate parsing:

```bash
docker compose run --rm \
  -v "$(pwd)/data:/data:ro" \
  app vendor-ingest /data/vendor-data.csv --dry-run
```

### 5. Stop services

```bash
docker compose down
```

---

## Windows

### 1. Install Ollama (script)

Open **PowerShell** as a normal user (winget does not require admin for per-user installs in many setups). From the repository root:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\scripts\install-ollama-windows.ps1
```

If `ollama` is not found after install, **close and reopen PowerShell** (or sign out), then run:

```powershell
ollama pull nomic-embed-text
ollama pull gemma4:e4b
```

If you cannot use winget, install from [Ollama for Windows](https://ollama.com/download/windows) and pull the same models.

Ensure the Ollama app is running (system tray) so it listens on `http://localhost:11434`.

### 2. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` as needed. Compose overrides `QDRANT_URL` and `OLLAMA_BASE_URL` for the **`api`** container and sets `VENDOR_LOOKUP_API_BASE_URL` for Streamlit.

### 3. Start Qdrant, API, and Streamlit

From the repository root in PowerShell:

```powershell
docker compose up --build -d
```

- Qdrant: `http://localhost:6333`
- Vendor API: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

### 4. Ingest vendor CSV (one-off)

```powershell
docker compose run --rm `
  -v "${PWD}/data:/data:ro" `
  app vendor-ingest /data/vendor-data.csv
```

Dry run:

```powershell
docker compose run --rm `
  -v "${PWD}/data:/data:ro" `
  app vendor-ingest /data/vendor-data.csv --dry-run
```

### 5. Stop services

```powershell
docker compose down
```

---

## Troubleshooting

- **API cannot reach Ollama**  
Confirm Ollama is running on the host (`http://localhost:11434`). On Docker Desktop for Mac/Windows, `host.docker.internal` should resolve inside the **`api`** container. On **Linux** hosts, `extra_hosts: host.docker.internal:host-gateway` in `docker-compose.yml` helps; ensure Docker supports it.
- **API cannot reach Qdrant**  
Ensure services are up: `docker compose ps`. The **`api`** service must use `QDRANT_URL=http://qdrant:6333` inside Compose (already set in `docker-compose.yml`).
- **Streamlit cannot reach the vendor API**  
Ensure the **`api`** container is healthy and port 8000 is published. Inside Compose, `VENDOR_LOOKUP_API_BASE_URL=http://api:8000` must match the API service name. The **`api`** service defines a Docker **healthcheck** against `GET /v1/health`; **`app`** waits for `api` to be healthy before starting. On the host, `./scripts/verify_stack.sh with-api` checks Qdrant, Ollama, and the vendor API (start `vendor-api` first).
- **Large CSV path**  
Adjust the `-v` host path and the path passed to `vendor-ingest` so they match the mount inside the container.
- **Models missing**  
Run `ollama list` on the host and compare names/tags to `EMBEDDING_MODEL` and `CHAT_MODEL` in `.env`.

---

## Optional: run ingest on the host (Python venv)

If you prefer not to run ingestion in Docker, use a local Python 3.11+ environment, `pip install -e .`, set `.env` with `QDRANT_URL=http://localhost:6333` and `OLLAMA_BASE_URL=http://localhost:11434`, start only Qdrant with `docker compose up -d qdrant`, then run `vendor-ingest` on the host. The Streamlit app can still run in Docker with Compose as above.