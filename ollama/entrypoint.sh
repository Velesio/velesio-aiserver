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
  if ollama list >/dev/null 2>&1; then
    echo "Ollama API is ready!"
    break
  fi
  sleep 1
done

# 3) Pull the model (if not already present)
echo "Checking if model exists: $OLLAMA_MODEL"
if ollama list | grep -q "$OLLAMA_MODEL"; then
  echo "✓ Model $OLLAMA_MODEL already exists locally, skipping pull"
else
  echo "Pulling model: $OLLAMA_MODEL"
  ollama pull "$OLLAMA_MODEL" || {
    echo "⚠️ Failed to pull $OLLAMA_MODEL — check your network or model name."
  }
fi

# 4) Pre-heat the model with retries and proper waiting
echo "Pre-heating model: $OLLAMA_MODEL (this may take 10-30 seconds...)"
WARMUP_SUCCESS=false
for attempt in {1..5}; do
  echo "  Warmup attempt $attempt/5..."
  
  # Use ollama run with a short prompt to warm up the model
  RESPONSE=$(ollama run "$OLLAMA_MODEL" "Hi" 2>&1)
  EXIT_CODE=$?
  
  if [[ $EXIT_CODE -eq 0 ]] && [[ -n "$RESPONSE" ]]; then
    echo "✓ Model pre-heated successfully!"
    echo "  Response: $(echo "$RESPONSE" | head -c 100)..."
    WARMUP_SUCCESS=true
    break
  else
    echo "  ⚠️ Warmup attempt $attempt failed (exit code: $EXIT_CODE), retrying in 3s..."
    sleep 3
  fi
done

if [[ "$WARMUP_SUCCESS" == "false" ]]; then
  echo "⚠️ All warmup attempts failed - model will load on first request"
fi

# 5) Wait on the Ollama server process
echo "Ollama server started..."
wait "$SERVER_PID"
