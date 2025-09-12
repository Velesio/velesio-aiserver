---
layout: page
title: Architecture
nav_order: 3
---

# Architecture Overview

Graycat AI Server follows a microservice architecture designed for scalability, reliability, and maintainability.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│  (Unity Games, Web Apps, Mobile Apps, CLI Tools, etc.)     │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST API
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   API Gateway                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   FastAPI   │ │    Auth     │ │    Request Validation   ││
│  │   Server    │ │  Middleware │ │      & Routing          ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │ Job Queue
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Message Broker                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   Redis Queue                           ││
│  │  • Job queuing & distribution                           ││
│  │  • Result storage & retrieval                           ││
│  │  • Worker coordination                                  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────┬───────────────────────────────┬───────────────────┘
          │                               │
          │ Pull Jobs                     │ Pull Jobs
          │                               │
┌─────────▼─────────────┐      ┌─────────▼─────────────────────┐
│    LLM Worker         │      │  Stable Diffusion Worker     │
│  ┌─────────────────┐  │      │  ┌─────────────────────────┐  │
│  │ undreamai_server│  │      │  │    Automatic1111        │  │
│  │ (llama.cpp fork)│  │      │  │      WebUI              │  │
│  └─────────────────┘  │      │  └─────────────────────────┘  │
│  ┌─────────────────┐  │      │  ┌─────────────────────────┐  │
│  │  GGUF Models    │  │      │  │  Stable Diffusion      │  │
│  │     (Text)      │  │      │  │      Models             │  │
│  └─────────────────┘  │      │  └─────────────────────────┘  │
└───────────────────────┘      └───────────────────────────────┘
          │                               │
          └─────────────┬─────────────────┘
                        │ Results
                        │
┌─────────────────────▼─────────────────────────────────────────┐
│                 Monitoring Stack                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │  Prometheus │ │   Grafana   │ │      Log Aggregation    │  │
│  │   Metrics   │ │ Dashboards  │ │        (Loki)           │  │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Gateway (FastAPI)

**Location**: `api/`

The API Gateway serves as the entry point for all client requests:

- **Authentication**: Bearer token validation
- **Request Validation**: Pydantic models ensure data integrity
- **Job Queuing**: Converts HTTP requests to Redis jobs
- **Response Handling**: Polls Redis for job results and returns to clients
- **Documentation**: Auto-generated OpenAPI docs at `/docs`

**Key Features**:
- Async/await for high concurrency
- Structured logging
- Health checks
- Rate limiting (configurable)
- CORS support for web clients

### 2. Message Broker (Redis)

**Technology**: Redis with RQ (Redis Queue)

Redis serves multiple roles:

- **Job Queue**: Stores pending inference jobs
- **Result Storage**: Temporary storage for completed results
- **Worker Coordination**: Manages worker pool and load balancing
- **Session Management**: Optional session state for stateful conversations

**Queue Structure**:
```
llama_queue:
├── pending_jobs    # Jobs waiting for workers
├── active_jobs     # Currently processing jobs  
├── completed_jobs  # Finished jobs (TTL: 1 hour)
└── failed_jobs     # Failed jobs for debugging
```

### 3. GPU Workers

#### LLM Worker (`gpu/llm.py`)

**Core Technology**: `undreamai_server` (custom llama.cpp fork)

- **Model Format**: GGUF (GPT-Generated Unified Format)
- **Inference Engine**: Custom llama.cpp binary optimized for undream.ai
- **GPU Acceleration**: CUDA with configurable layer offloading
- **Context Management**: Configurable context windows (2K-32K tokens)

**Features**:
- Streaming text generation
- Configurable sampling parameters
- Multi-turn conversation support
- Memory-efficient attention mechanisms

#### Stable Diffusion Worker (`gpu/sd.py`)

**Core Technology**: Automatic1111 WebUI

- **Model Format**: Safetensors, CKPT
- **Inference Engine**: Diffusers + PyTorch
- **Acceleration**: xFormers, Flash Attention
- **Extensions**: LoRA, ControlNet, VAE support

**Features**:
- Text-to-image generation
- Image-to-image transformation
- Inpainting and outpainting
- Batch processing
- Custom model loading

### 4. Monitoring Stack

#### Prometheus
- **Metrics Collection**: System, Redis, and custom application metrics
- **Alerting**: Configurable alerts for system health
- **Data Retention**: 15 days of metric history

#### Grafana
- **Dashboards**: Pre-configured panels for all services
- **Alerting**: Visual alerts with notification channels
- **Data Sources**: Prometheus, Loki logs

#### Exporters
- **Node Exporter**: System metrics (CPU, memory, disk)
- **Redis Exporter**: Queue depth, connection count
- **NVIDIA GPU Exporter**: GPU utilization, memory, temperature

## Data Flow

### Text Generation Request Flow

1. **Client Request**
   ```
   POST /completion
   Authorization: Bearer <token>
   {
     "prompt": "Write a story about...",
     "max_tokens": 150,
     "temperature": 0.7
   }
   ```

2. **API Processing**
   - Validate bearer token against `API_TOKENS`
   - Validate request schema with Pydantic
   - Generate unique job ID
   - Enqueue job to Redis `llama_queue`

3. **Worker Processing**
   - LLM worker polls Redis queue
   - Loads request parameters
   - Calls `undreamai_server` binary
   - Streams or batches response
   - Stores result in Redis with TTL

4. **Response**
   - API polls Redis for job completion
   - Returns structured OpenAI-compatible response
   - Cleans up job data

### Image Generation Request Flow

1. **Client Request**
   ```
   POST /sdapi/v1/txt2img
   Authorization: Bearer <token>
   {
     "prompt": "A futuristic cityscape",
     "width": 512,
     "height": 512,
     "steps": 20
   }
   ```

2. **Processing Similar to Text**, but:
   - Job routed to SD worker
   - Image generated by Automatic1111 WebUI
   - Result encoded as base64
   - Metadata included (seed, model, parameters)

## Deployment Modes

### Standalone Mode (`REMOTE=false`)
- All services run on single machine
- Redis exposed on localhost:6379
- Direct worker access on ports 1337/7860
- Ideal for development and small deployments

### Distributed Mode (`REMOTE=true`)
- Workers connect to remote Redis instance
- Horizontal scaling of GPU workers
- Load balancing across multiple machines
- Production-ready architecture

## Security Architecture

### Authentication
- **Bearer Token**: Simple, stateless authentication
- **Multi-tenant**: Support for multiple API keys
- **Rate Limiting**: Per-token request limits (optional)

### Network Security
- **Internal Communication**: Services communicate via Docker network
- **Firewall**: Only necessary ports exposed
- **TLS**: HTTPS termination at reverse proxy (nginx)

### Data Security
- **No Persistent Storage**: Requests/responses not logged by default
- **Memory Isolation**: Workers run in separate containers
- **Model Security**: Models stored in protected volumes

## Performance Characteristics

### Throughput
- **LLM**: 10-50 tokens/second (depending on model size)
- **Stable Diffusion**: 1-5 images/minute (depending on resolution)
- **Concurrent Requests**: Limited by GPU memory and worker count

### Latency
- **API Response**: <100ms for job queuing
- **LLM First Token**: 200-500ms (cold start: 2-5s)
- **SD Image**: 10-60 seconds depending on parameters

### Scalability
- **Horizontal**: Add more GPU workers
- **Vertical**: Increase GPU memory/compute
- **Queue Depth**: Redis handles thousands of queued jobs

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| API | FastAPI + Uvicorn | High-performance async web framework |
| Queue | Redis + RQ | Message broker and job queue |
| LLM Engine | undreamai_server | Custom llama.cpp fork |
| SD Engine | Automatic1111 WebUI | Feature-rich SD implementation |
| Monitoring | Prometheus + Grafana | Metrics and visualization |
| Orchestration | Docker Compose | Service coordination |
| Proxy | Nginx (optional) | Load balancing and TLS |

## Next Steps

- [API Reference](api-reference.html) - Detailed endpoint documentation
- [Deployment Guide](deployment.html) - Production deployment strategies
- [Component Documentation](components/) - Deep dive into each service