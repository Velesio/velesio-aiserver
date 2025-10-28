---
layout: page
title: Self Hosting Quickstart
nav_order: 3
---

## Prerequisites

Before you begin, ensure you have:

- **Docker** and **Docker Compose** installed
- **NVIDIA GPU** with CUDA support (for GPU acceleration)
- **NVIDIA Docker runtime** configured

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Velesio/Velesio-aiserver.git
cd Velesio-aiserver
```

### 2. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit the `.env` file with your settings:

```bash
# Startup Commands
STARTUP_COMMAND=./llama-server --model /app/data/models/text/model.gguf --host 0.0.0.0 --port 1337 --gpu-layers 37 --template chatml
SD_STARTUP_COMMAND=./venv/bin/python launch.py --listen --port 7860 --api --skip-torch-cuda-test --no-half-vae --medvram --xformers --skip-version-check

# Configuration
API=true # false does not connect llamacpp server to api
RUN_SD=true
REDIS_HOST=redis
REDIS_PASS=secure_redis_pass
API_TOKENS=secure_token,secure_token2

# Model URLs
MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q8_0.gguf
LLAMA_SERVER_URL=http://localhost:1337
SD_MODEL_URL=https://civitai.com/api/download/models/128713?type=Model&format=SafeTensor&size=pruned&fp=fp16
LORA_URL=https://civitai.com/api/download/models/110115?type=Model&format=SafeTensor
VAE_URL=https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors
```

You can check out different model templates in the model templates section.
The system will automatically download model from MODEL_RULs on first run, you can also optionally place models in:
- **LLamacpp models**: `gpu/data/models/text/model.gguf`
- **SD models**: `gpu/data/models/image/models/`

## Note about images and the llama.cpp binary

When building or running the GPU image you have two options:

- Full `Dockerfile` (default): includes the build toolchain and will compile the `llama-server` (llama.cpp) binary where it runs. This is useful if you don't have a prebuilt binary, but the build step increases startup time and requires more CPU/disk (~10gb).

- `Dockerfile.lite`: a much smaller runtime image that expects a prebuilt `llama-server` binary inside the image context. By convention place the binary at `data/binaries/llama-server` (or update your startup command to point to the actual filename). Make sure your `.dockerignore` does not exclude that path so the binary is included in the `.lite` build while still excluding large folders like `venv/`, `gpu/sd/` and `data/models/`.

### 3. Run

```bash
# API Only:
docker compose up -d

# LlamaCPP + SD worker:
docker compose --profile gpu up

# Ollama:
docker compose --profile ollama up

# Ollama + GPU Worker for FastAPI wrapper (RUN_OLLAMA=true in the .env):
docker compose --profile ollama --profile gpu up

# If you are locally developing you can use the --build flag to rebuild the images
docker compose up -d --build
```

### 4. Connect in Unity!

Refer to one of the Unity integrations sections to start using your AI Inference server in Unity.

## Test

Test your installation with a simple API call:

```bash
curl -X POST http://localhost:8000/completion \
  -H "Authorization: Bearer secure_token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms:",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

Expected response:
```json
{
  "choices": [
    {
      "text": "Quantum computing is a revolutionary approach to computation...",
      "finish_reason": "length"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 100,
    "total_tokens": 108
  }
}
```

## Service Access

Once running, you can access:

| Service | URL | Credentials |
|---------|-----|-------------|
| API Documentation | http://localhost:8000/docs | Bearer token required |
| LLamaCPP / UndreamAI Server | http://localhost:1337 | None |
| Stable Diffusion WebUI | http://localhost:7860 | None |
| Grafana Dashboard | http://localhost:3000 | admin/admin |
| Prometheus Metrics | http://localhost:9090 | None |
| Redis | localhost:6379 | None |


## Verification Checklist

✅ **Docker containers running**
```bash
docker-compose ps
# Should show: api, redis, Velesio-gpu all running
```

✅ **API responds to health check**
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

✅ **Models loaded successfully**
```bash
docker-compose logs velesio-gpu | grep -i "model"
# Should show model loading messages
```

✅ **Redis queue operational**
```bash
docker-compose logs redis
# Should show Redis server ready messages
```

## Next Steps

- Check out the Unity Integrations section for various integrations!
- [Architecture Overview](architecture.html) - Understand the system design
- [API Reference](api-reference.html) - Explore all available endpoints
- [Deployment Guide](deployment.html) - Production deployment strategies

## Troubleshooting

**Common Issues:**

- **GPU not detected**: Ensure NVIDIA Docker runtime is installed
- **Model download fails**: Check internet connection and disk space
- **API returns 401**: Verify `API_TOKENS` environment variable
- **Out of memory**: Reduce `GPU_LAYERS` or use smaller models

See the [Troubleshooting Guide](troubleshooting.html) for detailed solutions.