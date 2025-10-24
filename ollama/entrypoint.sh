#!/usr/bin/env bash
set -euo pipefail

# Defaults (can be overridden via environment)
OLLAMA_MODEL="${OLLAMA_MODEL:-gemma2:2b}"
OLLAMA_MODELS="${OLLAMA_MODELS:-/models}"
OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-30m}"

echo "=== Starting Ollama Server ==="
echo "Model directory: $OLLAMA_MODELS"
echo "Default model: $OLLAMA_MODEL"

# 1) Start Ollama server in the background
ollama serve &
SERVER_PID=$!

# 2) Wait for the API to become available
echo "Waiting for Ollama API to become ready..."
for i in {1..60}; do
  if curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama API is ready!"
    break
  fi
  sleep 1
done

# 3) Pull the model (if not already present)
echo "Pulling model: $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL" || {
  echo "⚠️ Failed to pull $OLLAMA_MODEL — check your network or model name."
}

# 4) Optional: Warm up the model once to keep it hot
echo "Warming up model: $OLLAMA_MODEL"
curl -sS http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$OLLAMA_MODEL\",\"prompt\":\" \"}" >/dev/null 2>&1 || true

# 5) Wait on the Ollama server process
echo "Ollama server started..."
wait "$SERVER_PID"
