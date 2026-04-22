# Deploy and run (macOS and Windows)

This project runs **Qdrant** and a **Streamlit** UI in **Docker**, with the **vendor API** implemented either in **Python (FastAPI)** or **C# (ASP.NET Core)** depending on the Compose file you use. **Ollama** runs on the host and is installed with the scripts in `scripts/` (platform-specific).

| Compose file | Qdrant (host ports) | API | Streamlit (host port) |
|--------------|---------------------|-----|------------------------|
| [`docker-compose.yml`](../docker-compose.yml) | 6333 / 6334 | **Python** `api` on **8000** | **8501** (→ `VENDOR_LOOKUP_API_BASE_URL=http://api:8000`) |
| [`docker-compose.csharp.yml`](../docker-compose.csharp.yml) | **6335 / 6336** (avoids clashing with the default stack) | **C#** `api-csharp` on **8001** | **8502** (→ `VENDOR_LOOKUP_API_BASE_URL=http://api-csharp:8001`) |

Ollama is not containerized. Both stacks set `QDRANT_URL=http://qdrant:6333` and `OLLAMA_BASE_URL=http://host.docker.internal:11434` inside the application containers so they reach Qdrant on the Docker network and Ollama on your machine.

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

Edit `.env` if needed (models, thresholds). For **Docker Compose**, you normally **do not** need to change `QDRANT_URL` or `OLLAMA_BASE_URL` in `.env` — the compose file overrides them for the `app` and `api` / `api-csharp` services.

### 3. Start Qdrant, API, and Streamlit

**Python API (default):** from the repository root:

```bash
docker compose up --build -d
```

- Qdrant HTTP API: `http://localhost:6333`
- Python API: `http://localhost:8000`
- Streamlit UI: `http://localhost:8501`

**C# API (alternate stack, different host ports):**

```bash
docker compose -f docker-compose.csharp.yml up --build -d
```

- Qdrant HTTP API (host): `http://localhost:6335`
- C# API: `http://localhost:8001` (Swagger: `/swagger`)
- Streamlit UI: `http://localhost:8502`

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

### 3. Start Qdrant, API, and Streamlit

**Python API (default):** from the repository root in PowerShell:

```powershell
docker compose up --build -d
```

- Qdrant: `http://localhost:6333`
- Python API: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

**C# API (alternate):**

```powershell
docker compose -f docker-compose.csharp.yml up --build -d
```

- Qdrant (host): `http://localhost:6335`
- C# API: `http://localhost:8001`
- Streamlit: `http://localhost:8502`

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
  Ensure both services are up: `docker compose ps` (or the same with `-f docker-compose.csharp.yml`). Inside Compose, services use `QDRANT_URL=http://qdrant:6333`. On the **host**, use `http://localhost:6333` for the default stack or `http://localhost:6335` when you started [`docker-compose.csharp.yml`](../docker-compose.csharp.yml).

- **Large CSV path**  
  Adjust the `-v` host path and the path passed to `vendor-ingest` so they match the mount inside the container.

- **Models missing**  
  Run `ollama list` on the host and compare names/tags to `EMBEDDING_MODEL` and `CHAT_MODEL` in `.env`.

---

## Optional: run ingest on the host (Python venv)

If you prefer not to run ingestion in Docker, use a local Python 3.11+ environment, `pip install -e "backend/python[dev]"` from the repo root, set `.env` with `QDRANT_URL` pointing at the Qdrant you started (`http://localhost:6333` for the default compose, or `http://localhost:6335` if only [`docker-compose.csharp.yml`](../docker-compose.csharp.yml) is up) and `OLLAMA_BASE_URL=http://localhost:11434`, then run `vendor-ingest` on the host. The Streamlit app can still run in Docker with either compose file as above.
