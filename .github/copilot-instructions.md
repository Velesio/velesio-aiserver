# velesio AI Server - AI Coding Agent Instructions

## Architecture Overview

This is a **microservice-based AI inference server** with Redis queue-based worker architecture:

- **`api/`**: FastAPI service handling HTTP requests, auth, and job queuing
- **`gpu/`**: Worker service with LLM and Stable Diffusion inference engines
  - Supports **llama.cpp** (standard `llama-server` binary) or **Ollama** for LLM
  - Uses `sd.py` for Stable Diffusion (shared across both LLM modes)
- **`ollama/`**: Optional Ollama container for easier model management
- **`redis`**: Message broker decoupling API from GPU workers using RQ (Redis Queue)
- **`monitoring/`**: Pre-configured Grafana/Prometheus stack with auto-provisioned dashboards
- **`nginx/`**: Reverse proxy (commented out by default in docker-compose)

**Key Communication Pattern**: API receives requests → validates tokens → pushes jobs to Redis → GPU workers pull and process → results returned via Redis.

## Critical File Structure

```
gpu/data/
├── models/text/model.gguf          # LLM model (auto-downloaded)
└── models/image/models/Stable-diffusion/  # SD models (auto-downloaded)
```

**Important**: This uses standard `llama-server` from llama.cpp with CUDA support, compiled during Docker image build.

## Environment Configuration Patterns

- **LLM Backend Selection**: 
  - `RUN_LLAMACPP=true` + `RUN_OLLAMA=false`: Use llama.cpp with custom binary
  - `RUN_OLLAMA=true` + `RUN_LLAMACPP=false`: Use Ollama for easier model management
  - Cannot run both simultaneously
- **Worker Mode**: `API=true` (worker connects to Redis) vs `API=false` (standalone with exposed ports)
- **Model Auto-Download**: `MODEL_URL`, `SD_MODEL_URL`, `LORA_URL`, `VAE_URL` trigger downloads in `entrypoint.sh` if models missing
- **Token Authentication**: `API_TOKENS` as comma-separated list, validated in `api/main.py` via Bearer token
- **Ollama Configuration**: `OLLAMA_SERVER_URL`, `OLLAMA_MODEL` when using Ollama mode

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
- Port 1337: LLaMA inference endpoint (when `API=false`)
- Port 7860: Stable Diffusion WebUI (when `RUN_SD=true`)
- Check worker logs: `docker logs velesio-gpu`
- Redis queue inspection: Connect to Redis on port 6379

### Model Management
- Text models (llama.cpp): Place `.gguf` files in `gpu/data/models/text/`
- Text models (Ollama): Pull via `docker exec velesio-ollama ollama pull <model>`
- Image models: Place `.safetensors`/`.ckpt` in `gpu/data/models/image/models/Stable-diffusion/`
- Volume-mounted at `/app/data` in containers
- Ollama models stored in `ollama/models/` (persistent)

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

**Binary Management**: Compiles `llama-server` from source with CUDA support in builder stage, copies binary to runtime image. Models are volume-mounted, not included in image.

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
- **Port conflicts**: 1337 (LLM), 7860 (SD), 6379 (Redis), 8000 (API), 11434 (Ollama)
- **Ollama issues**: Check container is running (`docker ps | grep ollama`), test connection (`curl http://localhost:11434/api/tags`)
- **Mode conflicts**: Can't run `RUN_OLLAMA=true` and `RUN_LLAMACPP=true` simultaneously