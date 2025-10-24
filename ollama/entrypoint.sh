#!/bin/sh
set -e

# Start Ollama server in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready (60 second timeout)
echo "Waiting for Ollama server..."
n=0
until curl -s http://localhost:11434/api/tags >/dev/null 2>&1 || [ $n -ge 60 ]; do
  n=$((n+1))
  sleep 1
done

if [ $n -ge 60 ]; then
  echo "Ollama failed to start"
  kill $OLLAMA_PID 2>/dev/null || true
  exit 1
fi

echo "Ollama server ready"

# Pull model if specified and not present
if [ -n "$OLLAMA_MODEL" ]; then
  echo "Checking for model: $OLLAMA_MODEL"
  
  if ! ollama list | grep -q "^$OLLAMA_MODEL"; then
    echo "Model $OLLAMA_MODEL not found. Pulling..."
    ollama pull "$OLLAMA_MODEL"
    echo "Model $OLLAMA_MODEL pulled successfully"
  else
    echo "Model $OLLAMA_MODEL already exists"
  fi
  
  # Preload model into memory
  echo "Preloading model $OLLAMA_MODEL..."
  printf "" | ollama run "$OLLAMA_MODEL" >/dev/null 2>&1 || true
  echo "Model $OLLAMA_MODEL ready for inference"
fi

# Keep container running
echo "Ollama service ready. Waiting for requests..."
wait $OLLAMA_PID
