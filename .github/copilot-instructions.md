# Graycat AI Server - AI Coding Agent Instructions

## Architecture Overview

This is a **microservice-based AI inference server** with Redis queue-based worker architecture:

- **`api/`**: FastAPI service handling HTTP requests, auth, and job queuing
- **`gpu/`**: Worker service containing both LLM (`llm.py`) and Stable Diffusion (`sd.py`) inference engines
- **`redis`**: Message broker decoupling API from GPU workers using RQ (Redis Queue)
- **`monitoring/`**: Pre-configured Grafana/Prometheus stack with auto-provisioned dashboards
- **`nginx/`**: Reverse proxy (commented out by default in docker-compose)

**Key Communication Pattern**: API receives requests → validates tokens → pushes jobs to Redis → GPU workers pull and process → results returned via Redis.

## Critical File Structure

```
gpu/data/
├── llama/undreamai_server          # Custom llama.cpp binary (not standard)
├── models/text/model.gguf          # LLM model (auto-downloaded)
└── models/image/models/Stable-diffusion/  # SD models (auto-downloaded)
```

**Important**: This uses `undreamai_server` (custom llama.cpp fork), not standard llama.cpp. The binary is fetched via `gpu/data/llama/server_setup.sh`.

## Environment Configuration Patterns

- **Dual Mode Operation**: `REMOTE=true` (worker connects to remote Redis) vs `REMOTE=false` (standalone with exposed ports)
- **Model Auto-Download**: `MODEL_URL`, `SD_MODEL_URL`, `LORA_URL`, `VAE_URL` trigger downloads in `entrypoint.sh` if models missing
- **Token Authentication**: `API_TOKENS` as comma-separated list, validated in `api/main.py` via Bearer token

## Development Workflows

### Local Development
```bash
# 1. Setup models and binaries
cd gpu && ./data/llama/server_setup.sh

# 2. Configure environment
cp .env.example .env  # Edit tokens, model URLs

# 3. Build and run
docker-compose up -d --build
```

### GPU Worker Debugging
- Port 1337: LLaMA inference endpoint (when `REMOTE=false`)
- Port 7860: Stable Diffusion WebUI (when `RUN_SD=true`)
- Check worker logs: `docker logs graycat-gpu`
- Redis queue inspection: Connect to Redis on port 6379

### Model Management
- Text models: Place `.gguf` files in `gpu/data/models/text/`
- Image models: Place `.safetensors`/`.ckpt` in `gpu/data/models/image/models/Stable-diffusion/`
- Volume-mounted at `/app/data` in containers

## Project-Specific Conventions

### Error Handling Pattern
Both `llm.py` and `sd.py` use consistent error wrapping:
```python
try:
    # API call
    response.raise_for_status()
    return response.json()
except Exception as e:
    return {"error": str(e)}
```

### Redis Job Processing
- Queue name: `"llama_queue"` (hardcoded in `llm.py`)
- Jobs enqueued by API, processed by RQ workers
- Results stored in Redis with TTL for client polling

### Unity Integration Focus
- Endpoints designed for Unity Asset Store compatibility
- `/completion` endpoint specifically for "LLM for Unity" asset
- Base64 image returns for Stable Diffusion integration

## Docker Build Optimizations

**GPU Container**: Uses layer caching strategy
1. PyTorch/CUDA dependencies first (slow-changing)
2. Application requirements
3. Code last (fast-changing)

**Binary Management**: Only copies `undreamai_server` binary, excludes models from image (volume-mounted instead).

## Monitoring Stack

Access pre-configured dashboards:
- Grafana: http://localhost:3000 (admin/admin)
- Dashboards auto-load from `monitoring/grafana/dashboards/`
- Redis metrics via redis_exporter
- System metrics via node_exporter

Start with: `cd monitoring && docker-compose up -d`

## Common Debugging Points

- **Auth issues**: Check `API_TOKENS` environment variable
- **Model loading**: Verify URLs in `.env` and check `entrypoint.sh` logs
- **GPU allocation**: Ensure Docker has GPU access and `GPU_LAYERS` > 0
- **Queue issues**: Monitor Redis queue depth and worker status
- **Port conflicts**: 1337 (LLM), 7860 (SD), 6379 (Redis), 8000 (API)