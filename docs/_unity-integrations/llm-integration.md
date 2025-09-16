---
layout: page
title: LLM for Unity Integration
parent: Unity Integrations
nav_order: 1
---

# LLM for Unity Integration

A Unity package that connects [LLMUnity](https://github.com/undreamai/LLMUnity) to Graycat AI Server for seamless LLM integration.

## Technical Overview

This integration provides a bridge between Unity and Graycat AI Server's `/completion` endpoint:

```
Unity Game → LLMUnity Package → HTTP POST → Graycat AI Server → LLM Response
```

### API Integration

**Endpoint**: `POST /completion`

**Request Format**:
```json
{
  "prompt": "Your prompt text here",
  "max_tokens": 150,
  "temperature": 0.7
}
```

**Response Format**:
```json
{
  "text": "Generated response text",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 25,
    "total_tokens": 35
  }
}
```

### Unity Implementation

The integration configures LLMUnity to use Graycat AI Server as a remote endpoint instead of running local models:

```csharp
// Configure LLMUnity to use Graycat AI Server
var llmConfig = new LLMConfiguration
{
    remote = true,
    host = "your-graycat-server.com",
    port = 8000,
    endpoint = "/completion",
    apiKey = "your-api-token"
};
```

### Authentication

All requests include Bearer token authentication:
```
Authorization: Bearer your-api-token
```

### Benefits

- **No Local Processing**: Offloads LLM computation to dedicated GPU servers
- **Scalability**: Handle multiple Unity clients with distributed inference
- **Model Flexibility**: Switch between different LLM models server-side
- **Performance**: Optimized inference on dedicated hardware