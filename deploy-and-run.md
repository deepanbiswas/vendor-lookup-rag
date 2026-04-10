# Deploy and run (macOS and Windows)

This project runs **Qdrant** and the **Python Streamlit app** in **Docker**. **Ollama** runs on the host machine and is installed with the scripts in `scripts/` (platform-specific).

| Component | How it runs |
|-----------|-------------|
| Qdrant | Docker (`docker-compose.yml` → service `qdrant`) |
| Streamlit app | Docker (`docker-compose.yml` → service `app`) |
| Ollama | Host — install with `scripts/install-ollama-macos.sh` or `scripts/install-ollama-windows.ps1` |

The Compose file sets `QDRANT_URL=http://qdrant:6333` and `OLLAMA_BASE_URL=http://host.docker.internal:11434` for the app container so it talks to Qdrant on the Docker network and Ollama on your machine.

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

Edit `.env` if needed (models, thresholds). For **Docker Compose**, you normally **do not** need to change `QDRANT_URL` or `OLLAMA_BASE_URL` in `.env` — `docker-compose.yml` overrides them for the `app` service.

### 3. Start Qdrant and the app

From the repository root:

```bash
docker compose up --build -d
```

- Qdrant HTTP API: `http://localhost:6333`
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

Edit `.env` as needed. Compose still overrides `QDRANT_URL` and `OLLAMA_BASE_URL` for the `app` container.

### 3. Start Qdrant and the app

From the repository root in PowerShell:

```powershell
docker compose up --build -d
```

- Qdrant: `http://localhost:6333`
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

- **App cannot reach Ollama**  
  Confirm Ollama is running on the host (`http://localhost:11434`). On Docker Desktop for Mac/Windows, `host.docker.internal` should resolve inside containers. On **Linux** hosts, `extra_hosts: host.docker.internal:host-gateway` in `docker-compose.yml` helps; ensure Docker supports it.

- **App cannot reach Qdrant**  
  Ensure both services are up: `docker compose ps`. The app must use `QDRANT_URL=http://qdrant:6333` inside Compose (already set in `docker-compose.yml`).

- **Large CSV path**  
  Adjust the `-v` host path and the path passed to `vendor-ingest` so they match the mount inside the container.

- **Models missing**  
  Run `ollama list` on the host and compare names/tags to `EMBEDDING_MODEL` and `CHAT_MODEL` in `.env`.

---

## Optional: run ingest on the host (Python venv)

If you prefer not to run ingestion in Docker, use a local Python 3.11+ environment, `pip install -e .`, set `.env` with `QDRANT_URL=http://localhost:6333` and `OLLAMA_BASE_URL=http://localhost:11434`, start only Qdrant with `docker compose up -d qdrant`, then run `vendor-ingest` on the host. The Streamlit app can still run in Docker with Compose as above.
