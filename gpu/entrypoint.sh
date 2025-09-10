#!/bin/bash

if [ ! -f /app/data/models/text/model.gguf ]; then
    wget -O /app/data/models/text/model.gguf "$MODEL_URL"
fi

# Start Automatic1111 WebUI if RUN_SD is enabled
if [ "$RUN_SD" = "true" ]; then
    echo "🎨 Setting up Automatic1111 WebUI..."
    
    # Check if SD WebUI is already set up (look for launch.py)
    if [ ! -f "/app/data/sd/launch.py" ]; then
        echo "📦 Cloning Automatic1111 WebUI to /app/data/sd..."
        # Backup models directory if it exists
        if [ -d "/app/data/sd/models" ]; then
            echo "📦 Backing up existing models directory..."
            cp -r /app/data/sd/models /tmp/sd_models_backup
        fi
        # Remove incomplete installation and clone fresh
        rm -rf /app/data/sd
        git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git /app/data/sd
        # Restore models directory if backup exists
        if [ -d "/tmp/sd_models_backup" ]; then
            echo "📦 Restoring models directory..."
            rm -rf /app/data/sd/models
            mv /tmp/sd_models_backup /app/data/sd/models
        fi
    fi
    
    cd /app/data/sd
    
    # Set up Python virtual environment if not already done
    if [ ! -d "venv" ]; then
        echo "🐍 Creating Python virtual environment..."
        python3 -m venv venv
        ./venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    fi
    
    # Create models directory structure if not exists
    mkdir -p models/Stable-diffusion models/VAE models/Lora models/embeddings
    
    # Link your existing model to A1111's expected location
    if [ -f /app/data/models/image/dnd.safetensors ]; then
        echo "📦 Linking your DnD model..."
        ln -sf /app/data/models/image/dnd.safetensors models/Stable-diffusion/dnd.safetensors
    fi
    
    # Link any other models in your image folder
    for model in /app/data/models/image/*.safetensors /app/data/models/image/*.ckpt; do
        if [ -f "$model" ]; then
            basename_model=$(basename "$model")
            ln -sf "$model" "models/Stable-diffusion/$basename_model"
        fi
    done
    
    # Start A1111 with API enabled, no browser, and listen on all interfaces
    ./venv/bin/python launch.py \
        --listen --port 7860 --api  \
        --xformers --skip-torch-cuda-test \
        --no-half-vae --medvram &
    
    # Wait for A1111 to start up
    echo "⏳ Waiting for A1111 to start..."
    sleep 30
    cd /app
fi

# Start with minimal arguments and multiple slots for context management
./data/llama/undreamai_server \
    --model /app/data/models/text/model.gguf \
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