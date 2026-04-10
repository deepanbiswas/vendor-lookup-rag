#!/usr/bin/env bash
# Install Ollama on macOS (Homebrew) and pull models used by vendor-lookup-rag.
# Run from repo root: bash scripts/install-ollama-macos.sh

set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install from https://brew.sh then re-run this script."
  exit 1
fi

echo "Installing Ollama via Homebrew..."
brew install ollama

echo ""
echo "Starting Ollama service (background)..."
brew services start ollama 2>/dev/null || true

# Give the daemon a moment to listen on :11434
sleep 2

if ! command -v ollama >/dev/null 2>&1; then
  echo "ollama CLI not found in PATH. Open a new terminal or run: brew list ollama"
  exit 1
fi

echo ""
echo "Pulling embedding model (nomic-embed-text)..."
ollama pull nomic-embed-text

echo ""
echo "Pulling chat model (gemma4:e4b) — this may take a while..."
ollama pull gemma4:e4b

echo ""
echo "Done. Ollama should be available at http://localhost:11434"
echo "If pulls failed, ensure Ollama is running: brew services restart ollama"
echo "Optional: ollama list"
