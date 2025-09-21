---
layout: page
title: Getting Started
nav_order: 2
---

# Getting Started

This guide will help you set up and run Velesio AI Server locally for development or testing.

## Prerequisites

Before you begin, ensure you have:

- **Docker** and **Docker Compose** installed
- **NVIDIA GPU** with CUDA support (for GPU acceleration)
- **NVIDIA Docker runtime** configured
- At least **8GB RAM** and **4GB GPU memory**

### Verify GPU Setup

```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

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
# Required: Set your API tokens (comma-separated for multiple tokens)
API_TOKENS=your-secret-token-here,another-token

# Optional: Model URLs (will auto-download if not present)
MODEL_URL=https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/pytorch_model.bin
SD_MODEL_URL=https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt

# GPU Configuration
GPU_LAYERS=35  # Number of model layers to run on GPU
CUDA_VISIBLE_DEVICES=0  # GPU device ID

# Service Configuration
REMOTE=false  # Set to true for distributed setup
RUN_SD=true   # Enable Stable Diffusion
```

### 3. Model Setup (Optional)

The system will automatically download models on first run, but you can pre-download them:

```bash
# Setup LLM binary and models
cd gpu && ./data/llama/server_setup.sh
```

Manually place models in:
- **Text models**: `gpu/data/models/text/model.gguf`
- **Image models**: `gpu/data/models/image/models/Stable-diffusion/`

### 4. Build and Run

```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## First API Call

Test your installation with a simple API call:

```bash
curl -X POST http://localhost:8000/completion \
  -H "Authorization: Bearer your-secret-token-here" \
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
| Stable Diffusion WebUI | http://localhost:7860 | None |
| Grafana Dashboard | http://localhost:3000 | admin/admin |
| Prometheus Metrics | http://localhost:9090 | None |
| Redis | localhost:6379 | None |

## Development Mode

For development, you can run services individually:

### API Service Only
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### GPU Worker Only
```bash
cd gpu
pip install -r requirements.txt
python llm.py  # For LLM worker
python sd.py   # For Stable Diffusion worker
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_TOKENS` | Required | Comma-separated API tokens |
| `REMOTE` | `false` | Remote Redis connection mode |
| `RUN_SD` | `true` | Enable Stable Diffusion |
| `GPU_LAYERS` | `35` | GPU layers for LLM |
| `MODEL_URL` | None | Auto-download LLM model |
| `SD_MODEL_URL` | None | Auto-download SD model |

### Docker Compose Profiles

```bash
# Run only core services (API + GPU + Redis)
docker-compose --profile core up -d

# Run with monitoring
docker-compose --profile monitoring up -d

# Run everything
docker-compose up -d
```

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
docker-compose logs Velesio-gpu | grep -i "model"
# Should show model loading messages
```

✅ **Redis queue operational**
```bash
docker-compose logs redis
# Should show Redis server ready messages
```

## Next Steps

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