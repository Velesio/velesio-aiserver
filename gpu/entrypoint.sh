#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p /app/data/models/text
mkdir -p /app/data/models/image/models/Stable-diffusion
mkdir -p /app/data/models/image/models/VAE
mkdir -p /app/data/models/image/models/Lora
mkdir -p /app/data/models/image/models/embeddings
mkdir -p /app/data/sd

# Check if virtual environment exists, if not create it and install packages
if [ ! -d "/app/data/venv" ]; then
    echo "🐍 Creating virtual environment and installing Python packages..."
    python3 -m venv /app/data/venv
    source /app/data/venv/bin/activate
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install PyTorch and related packages with CUDA support
    echo "📦 Installing PyTorch with CUDA support..."
    pip install --no-cache-dir torch torchvision torchaudio xformers --index-url https://download.pytorch.org/whl/cu124
    
    # Install other requirements
    echo "📦 Installing remaining Python packages..."
    pip install --no-cache-dir -r /app/requirements.txt
    
    # Install additional dependencies that might be needed by Stable Diffusion
    echo "📦 Installing additional SD dependencies..."
    pip install --no-cache-dir click uvicorn fastapi
    
    echo "✅ Python packages installed to persistent volume"
else
    echo "🔄 Using existing virtual environment from persistent volume"
    source /app/data/venv/bin/activate
fi

# Wait for critical packages to be properly installed before proceeding
echo "🔍 Verifying Python environment setup..."
until /app/data/venv/bin/python -c "import torch, torchvision, gradio; print('Critical packages available')" 2>/dev/null; do
    echo "⏳ Waiting for package installation to complete..."
    sleep 5
done
echo "✅ Python environment verified - ready to proceed"

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
    export GIT_DISCOVERY_ACROSS_FILESYSTEM=1
    # Check if SD WebUI is already set up (look for launch.py)
    if [ ! -d "/app/data/sd" ] || [ ! -f "/app/data/sd/launch.py" ]; then
        echo "📦 Cloning Automatic1111 WebUI to /app/data/sd..."
        rm -rf /app/data/sd
        git clone --depth 1 https://github.com/AUTOMATIC1111/stable-diffusion-webui.git /app/data/sd
        
        # Remove .git directory to save space and avoid git issues
        rm -rf /app/data/sd/.git
        echo "✅ Automatic1111 WebUI cloned successfully"
    else
        echo "✅ Using existing Automatic1111 WebUI installation"
    fi
    
    cd /app/data/sd
    
    # Set up virtual environment if not already linked
    if [ ! -L "venv" ] && [ ! -d "venv" ]; then
        echo "🔗 Creating symlink to shared virtual environment..."
        ln -s /app/data/venv venv
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
        # Use our unified Wu-Tang venv - Cash Rules Everything Around Me!
        ./venv/bin/python launch.py \
            --listen --port 7860 --api --nowebui\
            --skip-torch-cuda-test \
            --no-half-vae --medvram \
            --xformers \
            --skip-version-check \
            --skip-install &
    fi
    
    # Wait for A1111 to start up
    echo "⏳ Waiting for A1111 to start..."
    sleep 30
    cd /app
fi

# Ensure virtual environment is activated for all subsequent operations
if [ -d "/app/data/venv" ]; then
    source /app/data/venv/bin/activate
fi

# Start with startup command from environment variable ONLY if RUN_LLAMACPP is enabled
if [ "${RUN_LLAMACPP:-true}" = "true" ]; then
    GIT_DISCOVERY_ACROSS_FILESYSTEM=1
    echo "🚀 Starting llama.cpp server..."
    eval "$STARTUP_COMMAND" &
    
    # Wait for server to start
    sleep 5
    
    # Start the Python LLM worker only if REMOTE=true
    if [ "$REMOTE" = "true" ]; then
        echo "🔌 Starting LLM worker connected to Redis..."
        /app/data/venv/bin/python llm.py &
    fi
else
    echo "⏭️  Skipping llama.cpp server startup (RUN_LLAMACPP=false)"
fi

# Start the SD worker only if RUN_SD=true AND REMOTE=true
if [ "$RUN_SD" = "true" ] && [ "$REMOTE" = "true" ]; then
    echo "🎨 Starting Stable Diffusion worker connected to Redis..."
    /app/data/venv/bin/python sd.py &
fi

wait