#!/bin/bash

if [ ! -f /app/models/model.gguf ]; then
    wget -O /app/models/model.gguf "$MODEL_URL"
fi

# Start Automatic1111 WebUI if RUN_SD is enabled
if [ "$RUN_SD" = "true" ]; then
    echo "🎨 Starting Automatic1111 WebUI..."
    cd /opt/automatic1111
    
    # Link your existing model to A1111's expected location
    if [ -f /app/models/image/dnd.safetensors ]; then
        echo "📦 Linking your DnD model..."
        ln -sf /app/models/image/dnd.safetensors models/Stable-diffusion/dnd.safetensors
    fi
    
    # Link any other models in your image folder
    for model in /app/models/image/*.safetensors /app/models/image/*.ckpt; do
        if [ -f "$model" ]; then
            basename_model=$(basename "$model")
            ln -sf "$model" "models/Stable-diffusion/$basename_model"
        fi
    done
    
    # Start A1111 with API enabled, no browser, and listen on all interfaces
    ./venv/bin/python launch.py \
        --listen --port 7860 --api --no-browser \
        --xformers --skip-torch-cuda-test \
        --no-half-vae --medvram &
    
    # Wait for A1111 to start up
    echo "⏳ Waiting for A1111 to start..."
    sleep 30
    cd /app
fi

# Start with minimal arguments and multiple slots for context management
./llama/undreamai_server \
    --model /app/models/text/model.gguf \
    --host 0.0.0.0 \
    --port "$PORT" \
    --gpu-layers "$GPU_LAYERS" \
    --template chatml &

# Wait for server to start
sleep 5

# Start the Python worker only if REMOTE=true
if [ "$REMOTE" = "true" ]; then
    python3 llm.py &
fi

# Start the SD worker only if RUN_SD=true
if [ "$RUN_SD" = "true" ]; then
    python3 sd.py &
fi

wait