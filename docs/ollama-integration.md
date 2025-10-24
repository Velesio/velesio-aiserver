---
layout: page
title: Ollama Integration
permalink: /ollama-integration/
nav_order: 5
---

# Ollama Integration

Use Ollama instead of llama.cpp for LLM inference while maintaining the same Redis queue-based architecture and API compatibility.

## Quick Start

### 1. Configure Environment

Add to your `.env` file:

```bash
# Enable Ollama mode
RUN_OLLAMA=true
OLLAMA_MODEL=gemma3:4b
OLLAMA_SERVER_URL=http://ollama:11434

# Disable llama.cpp
RUN_LLAMACPP=false

# Enable Redis workers
API=true
```

### 2. Pull Model

```bash
docker exec velesio-ollama ollama pull gemma3:4b
docker exec velesio-ollama ollama list
```

### 3. Restart GPU Worker

```bash
docker-compose restart gpu
docker logs velesio-gpu -f
```

Expected output:
```
🦙 RUN_OLLAMA MODE ENABLED
🦙 Using external Ollama server at http://ollama:11434
🔌 Starting Ollama LLM worker connected to Redis...
```

## Architecture

The Ollama integration uses a drop-in replacement pattern:

```
API → Redis Queue → GPU Worker (Ollama Mode)
                    ├── ollama_llm.py → Ollama Server
                    └── sd.py         → SD WebUI (shared)
```

**Key Points:**
- `ollama_llm.py` replaces `llm.py` when `RUN_OLLAMA=true`
- `sd.py` is shared between both Ollama and llama.cpp modes
- Same Redis queues, same API endpoints - transparent to clients

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RUN_OLLAMA` | Yes | `false` | Enable Ollama mode |
| `OLLAMA_SERVER_URL` | No | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | No | `gemma2:2b` | Default model name |
| `RUN_LLAMACPP` | No | `true` | Disable when using Ollama |
| `RUN_SD` | No | `false` | Enable Stable Diffusion |
| `API` | Yes | - | Enable Redis workers |

### Docker Compose

The GPU service includes Ollama configuration:

```yaml
gpu:
  environment:
    - RUN_OLLAMA=${RUN_OLLAMA:-false}
    - OLLAMA_SERVER_URL=${OLLAMA_SERVER_URL:-http://ollama:11434}
    - OLLAMA_MODEL=${OLLAMA_MODEL:-gemma2:2b}
    - RUN_LLAMACPP=${RUN_LLAMACPP}
    - API=${API}
```

## Usage Modes

### Ollama LLM Only

```bash
RUN_OLLAMA=true
RUN_LLAMACPP=false
RUN_SD=false
API=true
```

Runs only Ollama LLM inference.

### Ollama + Stable Diffusion

```bash
RUN_OLLAMA=true
RUN_LLAMACPP=false
RUN_SD=true
API=true
```

Runs Ollama for text and SD WebUI for images.

### Traditional (llama.cpp)

```bash
RUN_OLLAMA=false
RUN_LLAMACPP=true
RUN_SD=true
API=true
```

Default mode using llama.cpp.

## API Compatibility

Ollama workers maintain full compatibility with existing Unity and API clients.

### Request Format

```json
{
  "prompt": "Hello, how are you?",
  "temperature": 0.7,
  "top_k": 40,
  "top_p": 0.9,
  "n_predict": 128,
  "stop": ["</s>", "\n\n"]
}
```

### Response Format

```json
{
  "content": "I'm doing well, thank you!",
  "multimodal": false,
  "slot_id": 0,
  "stop": true
}
```

### Parameter Mapping

The worker automatically converts between formats:

| Unity/LLaMA.cpp | Ollama | Description |
|-----------------|--------|-------------|
| `prompt` | `prompt` | Input text |
| `temperature` | `temperature` | Randomness (0-1) |
| `top_k` | `top_k` | Token sampling |
| `top_p` | `top_p` | Nucleus sampling |
| `n_predict` | `num_predict` | Max tokens |
| `repeat_penalty` | `repeat_penalty` | Repetition penalty |
| `seed` | `seed` | Random seed |
| `stop` | `stop` | Stop sequences |

## Available Models

### Recommended Models

| Model | Size | Use Case | GPU RAM |
|-------|------|----------|---------|
| `gemma2:2b` | ~1.5GB | Fast, lightweight | ~2GB |
| `gemma3:4b` | ~3GB | Balanced | ~4GB |
| `llama2:7b` | ~4GB | Good quality | ~6GB |
| `llama2:13b` | ~7GB | High quality | ~12GB |
| `mistral:7b` | ~4GB | Code-focused | ~6GB |

### Pull Models

```bash
# Pull any model
docker exec velesio-ollama ollama pull <model-name>

# List available models
docker exec velesio-ollama ollama list

# Update .env
OLLAMA_MODEL=<model-name>

# Restart worker
docker-compose restart gpu
```

## Testing

### Check Logs

```bash
docker logs velesio-gpu | grep OLLAMA
```

### Test Ollama Connection

```bash
curl http://localhost:11434/api/tags
```

### Send API Request

```bash
curl -X POST http://localhost:8000/completion \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "n_predict": 50}'
```

## Troubleshooting

### Ollama Server Connection Failed

**Check container is running:**
```bash
docker ps | grep ollama
curl http://localhost:11434/api/tags
```

**Check network connectivity:**
```bash
docker exec velesio-gpu curl http://ollama:11434/api/tags
```

### Worker Not Starting

**Check environment variables:**
```bash
docker exec velesio-gpu env | grep OLLAMA
docker exec velesio-gpu env | grep API
```

### Model Not Found

**Pull model first:**
```bash
docker exec velesio-ollama ollama pull gemma3:4b
docker exec velesio-ollama ollama list
```

### Redis Connection Failed

**Check Redis credentials:**
```bash
docker ps | grep redis
docker exec velesio-gpu env | grep REDIS
```

## Migration

### From llama.cpp to Ollama

1. Update `.env`:
   ```bash
   RUN_OLLAMA=true
   OLLAMA_MODEL=gemma3:4b
   RUN_LLAMACPP=false
   ```

2. Pull model:
   ```bash
   docker exec velesio-ollama ollama pull gemma3:4b
   ```

3. Restart:
   ```bash
   docker-compose restart gpu
   docker logs velesio-gpu | grep "OLLAMA MODE"
   ```

### From Ollama to llama.cpp

1. Update `.env`:
   ```bash
   RUN_OLLAMA=false
   RUN_LLAMACPP=true
   ```

2. Restart:
   ```bash
   docker-compose restart gpu
   ```

## Performance Comparison

| Feature | llama.cpp | Ollama |
|---------|-----------|--------|
| Model Management | Manual | Automatic |
| Setup Complexity | High | Low |
| Custom Binaries | ✅ | ❌ |
| Mac Support | Good | Better |
| GPU Acceleration | ✅ | ✅ |
| Context Slots | ✅ | ❌ |
| API Compatibility | Native | Converted |

### When to Use Ollama

- ✅ Easy model management
- ✅ Mac/Apple Silicon support
- ✅ Quick model switching
- ✅ Simple setup

### When to Use llama.cpp

- ✅ Custom server builds
- ✅ Slot-based caching
- ✅ Maximum performance tuning
- ✅ Advanced features

## Advanced Configuration

### Multiple Ollama Instances

```bash
# Worker 1
OLLAMA_SERVER_URL=http://ollama1:11434
OLLAMA_MODEL=gemma2:2b

# Worker 2
OLLAMA_SERVER_URL=http://ollama2:11434
OLLAMA_MODEL=llama2:13b
```

### Custom Model Parameters

Adjust via API request:
```json
{
  "prompt": "Your prompt",
  "temperature": 0.1,
  "top_k": 20,
  "top_p": 0.95,
  "repeat_penalty": 1.2
}
```

### Monitoring

```bash
# Worker status
docker logs velesio-gpu -f

# Ollama status
docker exec velesio-ollama ollama ps

# Redis queue depth
docker exec redis redis-cli -a $REDIS_PASS LLEN llama_queue

# GPU usage
nvidia-smi
```

## Implementation Details

### Components

- **`ollama_llm.py`**: Redis worker that wraps Ollama API
- **`sd.py`**: Shared SD worker (unchanged)
- **`entrypoint.sh`**: Detects `RUN_OLLAMA` and starts appropriate workers

### Dependencies

No additional dependencies required:
- `redis>=4.5.0`
- `rq==1.13.0`
- `requests`

### Worker Behavior

**ollama_llm.py:**
- Listens to Redis `gpu_tasks` channel
- Converts Unity/LLaMA.cpp format to Ollama format
- Supports streaming and non-streaming
- Handles: completion, template, tokenize, slots

**sd.py (shared):**
- Works with both Ollama and llama.cpp modes
- No modifications needed
- Handles: txt2img, img2img

## Important Notes

1. **Exclusive Modes**: Can't run Ollama and llama.cpp simultaneously in same worker
2. **Model Storage**: Ollama stores models separately from llama.cpp
3. **API Transparency**: Clients don't need to know which backend is used
4. **No Slot Support**: Ollama doesn't support llama.cpp's context slot caching

## Related Documentation

- [Architecture Overview]({{ site.baseurl }}/architecture/)
- [GPU Workers]({{ site.baseurl }}/components/gpu-workers/)
- [API Reference]({{ site.baseurl }}/api-reference/)
- [Troubleshooting]({{ site.baseurl }}/troubleshooting/)

---

**Need help?** Check the [troubleshooting guide]({{ site.baseurl }}/troubleshooting/) or review container logs.
