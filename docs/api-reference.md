---
layout: page
title: API Reference
nav_order: 4
---

# API Reference

Complete documentation for all Graycat AI Server endpoints.

## Authentication

All API endpoints require authentication using a Bearer token in the Authorization header:

```
Authorization: Bearer your-api-token-here
```

Configure tokens in the `.env` file:
```bash
API_TOKENS=token1,token2,token3
```

## Base URL

```
http://localhost:8000
```

For production deployments, replace with your actual domain.

## Text Generation Endpoints

### POST /completion

Generate text completion using the LLM model.

**Request Body:**
```json
{
  "prompt": "string",
  "max_tokens": 150,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stop": ["string"],
  "stream": false
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | Required | Input text to complete |
| `max_tokens` | integer | 150 | Maximum tokens to generate |
| `temperature` | float | 0.7 | Sampling temperature (0.0-2.0) |
| `top_p` | float | 0.9 | Nucleus sampling threshold |
| `top_k` | integer | 40 | Top-k sampling limit |
| `frequency_penalty` | float | 0.0 | Frequency penalty (-2.0 to 2.0) |
| `presence_penalty` | float | 0.0 | Presence penalty (-2.0 to 2.0) |
| `stop` | array | null | Stop sequences |
| `stream` | boolean | false | Enable streaming response |

**Response:**
```json
{
  "id": "cmpl-abc123",
  "object": "text_completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "text": "Generated text continues here...",
      "index": 0,
      "logprobs": null,
      "finish_reason": "length"
    }
  ],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 150,
    "total_tokens": 155
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/completion \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing:",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### POST /chat/completions

Chat completions with conversation history support.

**Request Body:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user", 
      "content": "Hello, how are you?"
    }
  ],
  "max_tokens": 150,
  "temperature": 0.7,
  "stream": false
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | array | Required | Conversation messages |
| `max_tokens` | integer | 150 | Maximum tokens to generate |
| `temperature` | float | 0.7 | Sampling temperature |
| `stream` | boolean | false | Enable streaming |

**Message Format:**
```json
{
  "role": "user|assistant|system",
  "content": "message content"
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 11,
    "total_tokens": 23
  }
}
```

## Image Generation Endpoints

### POST /sdapi/v1/txt2img

Generate images from text prompts using Stable Diffusion.

**Request Body:**
```json
{
  "prompt": "a beautiful landscape with mountains",
  "negative_prompt": "blurry, low quality",
  "width": 512,
  "height": 512,
  "steps": 20,
  "cfg_scale": 7.5,
  "sampler_name": "Euler a",
  "seed": -1,
  "batch_size": 1,
  "n_iter": 1
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | Required | Text description of desired image |
| `negative_prompt` | string | "" | What to avoid in the image |
| `width` | integer | 512 | Image width in pixels |
| `height` | integer | 512 | Image height in pixels |
| `steps` | integer | 20 | Number of sampling steps |
| `cfg_scale` | float | 7.5 | Classifier-free guidance scale |
| `sampler_name` | string | "Euler a" | Sampling method |
| `seed` | integer | -1 | Random seed (-1 for random) |
| `batch_size` | integer | 1 | Number of images per batch |
| `n_iter` | integer | 1 | Number of iterations |

**Response:**
```json
{
  "images": [
    "base64-encoded-image-data..."
  ],
  "parameters": {
    "prompt": "a beautiful landscape with mountains",
    "steps": 20,
    "seed": 1234567890,
    "width": 512,
    "height": 512
  },
  "info": "Additional generation info"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/sdapi/v1/txt2img \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a futuristic city at sunset",
    "width": 768,
    "height": 512,
    "steps": 25
  }'
```

### POST /sdapi/v1/img2img

Transform existing images using Stable Diffusion.

**Request Body:**
```json
{
  "init_images": ["base64-encoded-image"],
  "prompt": "turn this into a painting",
  "denoising_strength": 0.75,
  "width": 512,
  "height": 512,
  "steps": 20,
  "cfg_scale": 7.5
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `init_images` | array | Required | Base64 encoded input images |
| `prompt` | string | Required | Transformation description |
| `denoising_strength` | float | 0.75 | How much to change (0.0-1.0) |
| `width` | integer | 512 | Output width |
| `height` | integer | 512 | Output height |
| `steps` | integer | 20 | Sampling steps |
| `cfg_scale` | float | 7.5 | Guidance scale |

## Utility Endpoints

### GET /health

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "redis": "connected",
    "llm_worker": "ready",
    "sd_worker": "ready"
  }
}
```

### GET /models

List available models.

**Response:**
```json
{
  "text_models": [
    {
      "name": "llama-2-7b-chat",
      "size": "7B",
      "type": "chat",
      "loaded": true
    }
  ],
  "image_models": [
    {
      "name": "stable-diffusion-v1-5",
      "type": "checkpoint",
      "loaded": true
    }
  ]
}
```

### GET /queue/status

Check queue status and worker information.

**Response:**
```json
{
  "queue_depth": 3,
  "active_workers": 2,
  "pending_jobs": 1,
  "completed_jobs_24h": 150,
  "workers": [
    {
      "id": "worker-1",
      "type": "llm",
      "status": "busy",
      "current_job": "job-abc123"
    },
    {
      "id": "worker-2", 
      "type": "sd",
      "status": "idle"
    }
  ]
}
```

## Streaming Responses

For real-time text generation, set `stream: true` in the request:

**Example Streaming Request:**
```bash
curl -X POST http://localhost:8000/completion \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a story:", "stream": true}' \
  --no-buffer
```

**Streaming Response Format:**
```
data: {"choices":[{"text":"Once","index":0}]}

data: {"choices":[{"text":" upon","index":0}]}

data: {"choices":[{"text":" a","index":0}]}

data: [DONE]
```

## Error Responses

All endpoints return structured error responses:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The request was invalid",
    "details": "Additional error context"
  }
}
```

**Common Error Codes:**

| Code | Status | Description |
|------|--------|-------------|
| `unauthorized` | 401 | Invalid or missing API token |
| `invalid_request` | 400 | Malformed request body |
| `model_not_found` | 404 | Requested model not available |
| `queue_full` | 503 | Job queue at capacity |
| `internal_error` | 500 | Server error |

## Rate Limiting

API endpoints are subject to rate limiting:

- **Default**: 60 requests per minute per token
- **Burst**: Up to 10 concurrent requests
- **Headers**: Rate limit info included in response headers

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## Unity Integration

For Unity developers using the "LLM for Unity" asset:

**Configuration:**
```csharp
// In Unity LLM settings
API_URL = "http://your-server:8000"
API_KEY = "your-bearer-token"
MODEL = "completion" // Use the /completion endpoint
```

**Example Unity Code:**
```csharp
using UnityEngine;
using LLMUnity;

public class AIChat : MonoBehaviour 
{
    public LLMCharacter llmCharacter;
    
    async void Start() 
    {
        string response = await llmCharacter.Chat("Hello, AI!");
        Debug.Log(response);
    }
}
```

## SDKs and Libraries

### Python SDK
```python
import requests

class GraycatClient:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def complete(self, prompt, **kwargs):
        response = requests.post(
            f"{self.base_url}/completion",
            headers=self.headers,
            json={"prompt": prompt, **kwargs}
        )
        return response.json()

# Usage
client = GraycatClient("http://localhost:8000", "your-token")
result = client.complete("Explain AI:", max_tokens=100)
```

### JavaScript/Node.js
```javascript
class GraycatClient {
    constructor(baseUrl, apiToken) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiToken}`,
            'Content-Type': 'application/json'
        };
    }
    
    async complete(prompt, options = {}) {
        const response = await fetch(`${this.baseUrl}/completion`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ prompt, ...options })
        });
        return response.json();
    }
}

// Usage
const client = new GraycatClient('http://localhost:8000', 'your-token');
const result = await client.complete('Hello AI!');
```

## Next Steps

- [Getting Started](getting-started.html) - Set up your development environment  
- [Architecture](architecture.html) - Understand the system design
- [Deployment Guide](deployment.html) - Production deployment strategies