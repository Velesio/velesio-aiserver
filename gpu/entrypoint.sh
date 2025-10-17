#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p /app/data/models/text
mkdir -p /app/data/models/image/models/Stable-diffusion
mkdir -p /app/data/models/image/models/VAE
mkdir -p /app/data/models/image/models/Lora
mkdir -p /app/data/models/image/models/embeddings
mkdir -p /app/data/sd

if [ ! -f /app/data/models/text/model.gguf ]; then
    wget -O /app/data/models/text/model.gguf "$MODEL_URL"
fi

# Download image model if the models directory is empty
if [ -z "$(ls -A /app/data/models/image/models/Stable-diffusion 2>/dev/null)" ]; then
    if [ -n "$SD_MODEL_URL" ]; then
        echo "📦 Downloading Stable Diffusion model..."
        # Extract filename from URL or use default
        MODEL_FILENAME=$(basename "$SD_MODEL_URL" | cut -d'?' -f1)
        if [[ "$MODEL_FILENAME" != *.safetensors && "$MODEL_FILENAME" != *.ckpt ]]; then
            MODEL_FILENAME="sd-model.safetensors"
        fi
        wget -O "/app/data/models/image/models/Stable-diffusion/$MODEL_FILENAME" "$SD_MODEL_URL"
    fi
fi

# Download LoRA model if URL is provided
if [ -n "$LORA_URL" ] && [ ! -f "/app/data/models/image/models/Lora/lora-model.safetensors" ]; then
    echo "📦 Downloading LoRA model..."
    LORA_FILENAME=$(basename "$LORA_URL" | cut -d'?' -f1)
    if [[ "$LORA_FILENAME" != *.safetensors && "$LORA_FILENAME" != *.ckpt ]]; then
        LORA_FILENAME="lora-model.safetensors"
    fi
    wget -O "/app/data/models/image/models/Lora/$LORA_FILENAME" "$LORA_URL"
fi

# Download VAE model if URL is provided
if [ -n "$VAE_URL" ] && [ ! -f "/app/data/models/image/models/VAE/vae-model.safetensors" ]; then
    echo "📦 Downloading VAE model..."
    # Handle the VAE_URL which has extra parameters
    VAE_CLEAN_URL=$(echo "$VAE_URL" | cut -d' ' -f1)
    VAE_FILENAME=$(basename "$VAE_CLEAN_URL")
    if [[ "$VAE_FILENAME" != *.safetensors && "$VAE_FILENAME" != *.ckpt ]]; then
        VAE_FILENAME="vae-model.safetensors"
    fi
    wget -O "/app/data/models/image/models/VAE/$VAE_FILENAME" "$VAE_CLEAN_URL"
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
        git clone --depth 1 https://github.com/AUTOMATIC1111/stable-diffusion-webui.git /app/data/sd
        
        # Remove ALL .git folders to avoid git repository issues completely
        find /app/data/sd -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
        
        # Restore models directory if backup exists
        if [ -d "/tmp/sd_models_backup" ]; then
            echo "📦 Restoring models directory..."
            rm -rf /app/data/sd/models
            mv /tmp/sd_models_backup /app/data/sd/models
        fi
    fi
    
    cd /app/data/sd
    
    # Fix Git ownership issues before any Git operations
    git config --global --add safe.directory '*'
    git config --global user.name "Docker User"
    git config --global user.email "docker@example.com"
    
    # Set up Python virtual environment if not already done
    if [ ! -d "venv" ]; then
        echo "🐍 Creating Python virtual environment..."
        python3 -m venv venv --system-site-packages
        # Install any additional A1111-specific packages if needed
        ./venv/bin/pip install --upgrade pip
    fi
    
    # Create webui-user.sh for optimal settings WITH xformers
    cat > webui-user.sh << 'EOF'
#!/bin/bash
export COMMANDLINE_ARGS="--skip-version-check --xformers"
export TORCH_COMMAND="pip install torch torchvision torchaudio xformers --index-url https://download.pytorch.org/whl/cu124"
EOF
    chmod +x webui-user.sh
    
    # Set environment variables for optimal performance
    export COMMANDLINE_ARGS="--skip-version-check --xformers"
    
    # Create models directory structure if not exists
    mkdir -p models/Stable-diffusion models/VAE models/Lora models/embeddings
    
    # Symlink the entire models folder from /data/models/image/models to SD models folder
    if [ -d "/app/data/models/image/models" ]; then
        echo "📁 Symlinking models directory from /app/data/models/image/models to SD models folder..."
        # Remove existing models directory if it exists and is not a symlink
        if [ -d "models" ] && [ ! -L "models" ]; then
            echo "📁 Backing up existing models directory..."
            mv models models_backup_$(date +%s)
        fi
        # Create the symlink
        ln -sfn /app/data/models/image/models models
    fi
    
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
    
    # Start A1111 with command from environment variable
    if [ -n "$SD_STARTUP_COMMAND" ]; then
        eval "$SD_STARTUP_COMMAND" &
    else
        # Fallback to default command if SD_STARTUP_COMMAND is not set
        ./venv/bin/python launch.py \
            --listen --port 7860 --api --nowebui\
            --skip-torch-cuda-test \
            --no-half-vae --medvram \
            --xformers \
            --skip-version-check &
    fi
    
    # Wait for A1111 to start up
    echo "⏳ Waiting for A1111 to start..."
    sleep 30
    cd /app
fi

# Start with startup command from environment variable
eval "$STARTUP_COMMAND" &

# Wait for server to start
sleep 5

# Start the Python worker only if REMOTE=true
if [ "$REMOTE" = "true" ]; then
    python3 llm.py &
fi

# Start the SD worker only if RUN_SD=true AND REMOTE=true
if [ "$RUN_SD" = "true" ] && [ "$REMOTE" = "true" ]; then
    python3 sd.py &
fi

wait