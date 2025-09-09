#!/bin/bash

if [ ! -f /app/models/model.gguf ]; then
    wget -O /app/models/model.gguf "$MODEL_URL"
fi

# Start with minimal arguments and multiple slots for context management
./undreamai_server \
    --model /app/models/model.gguf \
    --host 0.0.0.0 \
    --port "$PORT" \
    --gpu-layers "$GPU_LAYERS" \
    --template chatml &

# Wait for server to start
sleep 5

# Start the Python worker only if REMOTE=true
if [ "$REMOTE" = "true" ]; then
    python3 worker.py &
fi

wait