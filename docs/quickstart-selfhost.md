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
STARTUP_COMMAND=./undreamai_server --model /app/data/models/text/model.gguf --host 0.0.0.0 --port 1337 --gpu-layers 37 --template chatml
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

### 3. (Optional) Self Hosted Setup Configuration

The UndreamAI server binaries are included in the public images, but if you are rebuilding the image you should include them, you can do so with. UndreamAI is used for Unity compatibility but the application works fine with the defualt llamacpp server as well.

```bash
# Setup LLM binary and models
cd gpu && ./data/llama/server_setup.sh
```
The system will automatically download model from MODEL_RULs on first run, you can also optionally place models in:
- **LLamacpp models**: `gpu/data/models/text/model.gguf`
- **SD models**: `gpu/data/models/image/models/`

### 4. Run

```bash
# Start all services
docker-compose up -d

# (Optional) Rebuild images
docker-compose up --build -d 

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Connect in Unity!

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