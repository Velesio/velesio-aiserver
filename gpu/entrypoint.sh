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
    if python3 -m venv /app/data/venv; then
        source /app/data/venv/bin/activate
        
        # Upgrade pip first
        pip install --upgrade pip
        
        # Install other requirements
        echo "📦 Installing remaining Python packages..."
        pip install --no-cache-dir -r /app/requirements.txt
            
        echo "✅ Python packages installed to persistent volume"
    else
        echo "❌ Failed to create virtual environment. Exiting."
        exit 1
    fi
else
    echo "🔄 Using existing virtual environment from persistent volume"
    source /app/data/venv/bin/activate
fi

# Wait for critical packages to be properly installed before proceeding
echo "🔍 Verifying Python environment setup..."
if /app/data/venv/bin/python -c "import torch, torchvision, gradio; print('Critical packages available')" 2>/dev/null; then
    echo "✅ Python environment verified - ready to proceed"
else
    echo "❌ Critical packages not available. Checking what was installed..."
    /app/data/venv/bin/python -c "import sys; print('Python version:', sys.version)" 2>/dev/null || echo "Python not available"
    /app/data/venv/bin/python -c "import torch; print('Torch available')" 2>/dev/null || echo "Torch not available"
    /app/data/venv/bin/python -c "import torchvision; print('Torchvision available')" 2>/dev/null || echo "Torchvision not available"
    /app/data/venv/bin/python -c "import gradio; print('Gradio available')" 2>/dev/null || echo "Gradio not available"
    echo "❌ Exiting due to missing critical packages"
    exit 1
fi

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

# Check if RUN_OLLAMA mode is enabled
if [ "${RUN_OLLAMA:-false}" = "true" ]; then
    echo "🦙 OLLAMA MODE ENABLED"
    echo "🦙 Using external Ollama server at ${OLLAMA_SERVER_URL:-http://localhost:11434}"
    
    # Start Ollama LLM worker if API=true
    if [ "$API" = "true" ]; then
        echo "🔌 Starting Ollama LLM worker connected to Redis..."
        /app/data/venv/bin/python ollama_llm.py &
    fi
    
    echo "✅ Ollama LLM worker started"
else
    # Original LLaMA.cpp startup logic
    # Start with startup command from environment variable ONLY if RUN_LLAMACPP is enabled
    if [ "${RUN_LLAMACPP:-true}" = "true" ]; then
                # Ensure llama-server binary exists in persistent folder; if not, build it there
                BINARY_DIR="/app/data/binaries"
                BINARY_PATH="$BINARY_DIR/llama-server"
                mkdir -p "$BINARY_DIR"
                if [ ! -x "$BINARY_PATH" ]; then
                        echo "🔨 llama-server not found in $BINARY_DIR — building from source (CPU-only, conservative flags)..."
                        echo "🔧 Build dependencies should be installed in the Docker image. Proceeding to build."

                        TMPDIR=$(mktemp -d)
                        git clone https://github.com/ggml-org/llama.cpp.git "$TMPDIR/llama.cpp" || { echo "❌ git clone failed"; exit 1; }
                        mkdir -p "$TMPDIR/llama.cpp/build" && cd "$TMPDIR/llama.cpp/build" || exit 1

                                    # Decide whether to build with CUDA support.
                                    # Use nvcc detection or FORCE_CUDA=1 to enable CUDA build when available.
                                    if command -v nvcc >/dev/null 2>&1 || [ "${FORCE_CUDA:-0}" = "1" ]; then
                                            echo "🔌 nvcc detected or FORCE_CUDA=1 — building with CUDA support"
                                            BUILD_CUDA=ON
                                            # Use native tuning when building with CUDA for best performance on the build host
                                            CFLAGS='-O3 -march=native'
                                            CXXFLAGS="$CFLAGS"
                                    else
                                            echo "⚙️  nvcc not detected — building CPU-only portable binary (conservative flags)"
                                            BUILD_CUDA=OFF
                                            # Conservative CPU flags to avoid illegal-instruction on varied hosts
                                            CFLAGS='-O3 -march=x86-64 -mtune=generic -mno-avx -mno-avx2'
                                            CXXFLAGS="$CFLAGS"
                                    fi

                                    cmake .. \
                                        -DCMAKE_BUILD_TYPE=Release \
                                        -DGGML_CUDA=${BUILD_CUDA} \
                                        -DGGML_NATIVE=OFF \
                                        -DBUILD_SHARED_LIBS=OFF \
                                        -DCMAKE_C_FLAGS="$CFLAGS" \
                                        -DCMAKE_CXX_FLAGS="$CXXFLAGS" \
                                        || { echo "❌ cmake configure failed"; exit 1; }

                        cmake --build . --config Release --target llama-server -j"$(nproc)" || { echo "❌ build failed"; exit 1; }
                        strip ./bin/llama-server || true
                        mv ./bin/llama-server "$BINARY_PATH"
                        chmod +x "$BINARY_PATH"
                        cd /app
                        rm -rf "$TMPDIR"
                        echo "✅ llama-server built and available at $BINARY_PATH"
                else
                        echo "✅ Using existing llama-server at $BINARY_PATH"
                fi

        GIT_DISCOVERY_ACROSS_FILESYSTEM=1
        echo "🚀 Starting llama.cpp server..."

        # Prefer binary in persistent folder. If STARTUP_COMMAND references 'llama-server' replace it,
        # otherwise build a default command using the persistent binary.
        if [ -n "$STARTUP_COMMAND" ]; then
            # If the user provided a STARTUP_COMMAND that references 'llama-server',
            # replace the command token with the persistent binary while preserving args.
            if echo "$STARTUP_COMMAND" | grep -q "llama-server"; then
                ARGS="${STARTUP_COMMAND#*llama-server}"
                CMD="$BINARY_PATH$ARGS"
            else
                # STARTUP_COMMAND doesn't reference llama-server: run it as-is
                CMD="$STARTUP_COMMAND"
            fi
        else
            CMD="$BINARY_PATH --model /app/data/models/text/model.gguf --host 0.0.0.0 --port 1337"
        fi
        eval "$CMD" &

        # Wait for server to start
        sleep 5

        # Start the Python LLM worker only if API=true
        if [ "$API" = "true" ]; then
            echo "🔌 Starting LLM worker connected to Redis..."
            /app/data/venv/bin/python llm.py &
        fi
    else
        echo "⏭️  Skipping llama.cpp server startup (RUN_LLAMACPP=false)"
    fi
fi

# Start the SD worker (works with both Ollama and llama.cpp modes)
if [ "$RUN_SD" = "true" ] && [ "$API" = "true" ]; then
    echo "🎨 Starting Stable Diffusion worker connected to Redis..."
    /app/data/venv/bin/python sd.py &
fi

wait