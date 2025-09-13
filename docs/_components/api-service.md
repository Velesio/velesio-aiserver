---
layout: page
title: API Service
parent: Components
nav_order: 1
---

# API Service

The API service is a FastAPI-based web server that handles HTTP requests and manages job queuing to GPU workers.

## Overview

**Location**: `api/`  
**Technology**: FastAPI + Uvicorn  
**Port**: 8000  
**Container**: `graycat-api`

The API service serves as the gateway between client applications and the AI inference workers, providing:

- HTTP/REST endpoint handling
- Bearer token authentication
- Request validation and preprocessing
- Redis job queue management
- Response formatting and delivery

## Architecture

```
Client Request
      ↓
┌─────────────────┐
│  FastAPI App    │
│                 │
│ ┌─────────────┐ │
│ │   Auth      │ │ ← Bearer token validation
│ │ Middleware  │ │
│ └─────────────┘ │
│                 │
│ ┌─────────────┐ │
│ │ Request     │ │ ← Pydantic validation
│ │ Validation  │ │
│ └─────────────┘ │
│                 │
│ ┌─────────────┐ │
│ │   Redis     │ │ ← Job queue management
│ │   Client    │ │
│ └─────────────┘ │
└─────────────────┘
      ↓
   Redis Queue
```

## Key Components

### 1. FastAPI Application (`main.py`)

The main application file defines all endpoints and middleware:

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import redis.asyncio as redis

app = FastAPI(
    title="Graycat AI Server",
    description="Microservice-based AI inference server",
    version="1.0.0"
)

security = HTTPBearer()
```

### 2. Authentication Middleware

Token-based authentication using environment variables:

```python
API_TOKENS = os.getenv("API_TOKENS", "").split(",")

async def verify_token(token: HTTPAuthorizationCredentials = Depends(security)):
    if token.credentials not in API_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.credentials
```

### 3. Request Models

Pydantic models ensure type safety and validation:

```python
class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 150
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = 150
    temperature: float = 0.7
    stream: bool = False
```

### 4. Redis Integration

Job queue management using Redis:

```python
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

async def enqueue_job(job_type: str, job_data: dict) -> str:
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "type": job_type,
        "data": job_data,
        "timestamp": time.time()
    }
    
    await redis_client.lpush("llama_queue", json.dumps(job))
    return job_id
```

## API Endpoints

### Text Generation

#### POST /completion

OpenAI-compatible text completion endpoint:

```python
@app.post("/completion")
async def completion(
    request: CompletionRequest,
    token: str = Depends(verify_token)
):
    # Enqueue job to Redis
    job_id = await enqueue_job("completion", request.dict())
    
    # Poll for results
    result = await poll_job_result(job_id)
    
    return {
        "id": f"cmpl-{job_id}",
        "object": "text_completion",
        "created": int(time.time()),
        "choices": [{
            "text": result["text"],
            "index": 0,
            "finish_reason": result.get("finish_reason", "stop")
        }],
        "usage": result.get("usage", {})
    }
```

#### POST /chat/completions

Chat-style completion with conversation history:

```python
@app.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    token: str = Depends(verify_token)
):
    # Convert chat messages to prompt
    prompt = format_chat_prompt(request.messages)
    
    # Create completion request
    completion_req = CompletionRequest(
        prompt=prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        stream=request.stream
    )
    
    # Process similar to /completion
    job_id = await enqueue_job("chat_completion", completion_req.dict())
    result = await poll_job_result(job_id)
    
    return format_chat_response(result, job_id)
```

### Image Generation

#### POST /sdapi/v1/txt2img

Stable Diffusion text-to-image generation:

```python
@app.post("/sdapi/v1/txt2img")
async def txt2img(
    request: Txt2ImgRequest,
    token: str = Depends(verify_token)
):
    job_id = await enqueue_job("txt2img", request.dict())
    result = await poll_job_result(job_id, timeout=300)  # Longer timeout for images
    
    return {
        "images": result["images"],
        "parameters": result["parameters"],
        "info": result.get("info", "")
    }
```

### Utility Endpoints

#### GET /health

Service health check:

```python
@app.get("/health")
async def health():
    try:
        # Check Redis connection
        await redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    # Check worker status
    worker_count = await redis_client.llen("llama_queue")
    
    return {
        "status": "healthy" if redis_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "redis": redis_status,
            "queue_depth": worker_count
        }
    }
```

#### GET /models

List available models:

```python
@app.get("/models")
async def list_models(token: str = Depends(verify_token)):
    # Query workers for available models
    models_info = await get_worker_models()
    
    return {
        "text_models": models_info.get("text", []),
        "image_models": models_info.get("image", [])
    }
```

## Job Management

### Job Queuing

Jobs are queued in Redis with the following structure:

```python
job = {
    "id": "uuid-string",
    "type": "completion|chat_completion|txt2img|img2img",
    "data": {
        # Request parameters
    },
    "timestamp": 1640995200.0,
    "priority": 1  # Optional priority
}
```

### Result Polling

The API polls Redis for job completion:

```python
async def poll_job_result(job_id: str, timeout: int = 60) -> dict:
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check for result
        result_key = f"result:{job_id}"
        result = await redis_client.get(result_key)
        
        if result:
            # Parse and return result
            return json.loads(result)
        
        # Wait before next poll
        await asyncio.sleep(0.5)
    
    raise HTTPException(status_code=408, detail="Request timeout")
```

### Streaming Responses

For streaming text generation:

```python
@app.post("/completion")
async def completion_stream(request: CompletionRequest):
    if not request.stream:
        return await completion(request)
    
    # Server-Sent Events streaming
    async def generate():
        job_id = await enqueue_job("completion_stream", request.dict())
        
        async for chunk in poll_streaming_result(job_id):
            yield f"data: {json.dumps(chunk)}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_TOKENS` | Required | Comma-separated API tokens |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | None | Redis password |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `["*"]` | CORS allowed origins |
| `MAX_QUEUE_SIZE` | `1000` | Maximum queue depth |
| `REQUEST_TIMEOUT` | `60` | Default request timeout |

### Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Non-root user
RUN useradd -m -u 1000 apiuser
USER apiuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Features

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/completion")
@limiter.limit("60/minute")
async def completion(request: CompletionRequest):
    # Endpoint implementation
```

### Input Validation

```python
class CompletionRequest(BaseModel):
    prompt: str = Field(..., max_length=10000, description="Input prompt")
    max_tokens: int = Field(150, ge=1, le=4000, description="Maximum tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Monitoring and Logging

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

@app.post("/completion")
async def completion(request: CompletionRequest):
    logger.info(
        "completion_request",
        prompt_length=len(request.prompt),
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Performance Optimization

### Connection Pooling

```python
import aioredis

redis_pool = aioredis.ConnectionPool.from_url(
    "redis://redis:6379",
    max_connections=100,
    retry_on_timeout=True
)

redis_client = aioredis.Redis(connection_pool=redis_pool)
```

### Async/Await Usage

```python
@app.post("/completion")
async def completion(request: CompletionRequest):
    # Non-blocking Redis operations
    job_id = await enqueue_job("completion", request.dict())
    
    # Concurrent job polling
    result = await asyncio.wait_for(
        poll_job_result(job_id),
        timeout=request.timeout or 60
    )
    
    return format_response(result)
```

### Caching

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_completion(prompt_hash: str) -> Optional[dict]:
    # Cache frequently requested completions
    pass

async def completion_with_cache(request: CompletionRequest):
    prompt_hash = hashlib.md5(request.prompt.encode()).hexdigest()
    
    # Check cache first
    cached = get_cached_completion(prompt_hash)
    if cached:
        return cached
    
    # Process normally and cache result
    result = await process_completion(request)
    cache_result(prompt_hash, result)
    return result
```

## Testing

### Unit Tests

```python
import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

def test_completion_endpoint():
    response = client.post(
        "/completion",
        headers={"Authorization": "Bearer test-token"},
        json={
            "prompt": "Hello, world!",
            "max_tokens": 50
        }
    )
    assert response.status_code == 200
    assert "choices" in response.json()

def test_invalid_token():
    response = client.post(
        "/completion",
        headers={"Authorization": "Bearer invalid-token"},
        json={"prompt": "Hello"}
    )
    assert response.status_code == 401
```

### Integration Tests

```python
async def test_redis_integration():
    # Test Redis connection
    await redis_client.ping()
    
    # Test job queuing
    job_id = await enqueue_job("test", {"data": "test"})
    assert job_id is not None
    
    # Test job retrieval
    queue_length = await redis_client.llen("llama_queue")
    assert queue_length > 0
```

## Deployment

### Production Configuration

```yaml
# docker-compose.prod.yml
services:
  api:
    image: graycathq/graycat-api:latest
    restart: unless-stopped
    environment:
      - API_TOKENS=${API_TOKENS}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Scaling

```bash
# Horizontal scaling
docker-compose up -d --scale api=5

# Load balancing with nginx
upstream api_backend {
    server api_1:8000;
    server api_2:8000;
    server api_3:8000;
}
```

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**
   - Check Redis service status
   - Verify network connectivity
   - Check authentication credentials

2. **High Memory Usage**
   - Monitor request queue size
   - Implement request timeouts
   - Add memory limits to containers

3. **Slow Response Times**
   - Check GPU worker availability
   - Monitor Redis queue depth
   - Optimize database queries

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add request/response logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response
```

## Next Steps

- [GPU Workers](gpu-workers.html) - Learn about LLM and SD workers
- [Redis Queue](redis-queue.html) - Understand job queue management
- [Monitoring](monitoring.html) - Set up observability