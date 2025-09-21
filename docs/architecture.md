---
layout: page
title: Architecture
nav_order: 3
---

# Architecture Overview

velesio AI Server follows a microservice architecture designed for scalability, reliability, and maintainability.

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

## Independent Components

velesio AI Server consists of **three independent, deployable components** that can run together or separately:

| Component | Description | Documentation |
|-----------|-------------|---------------|
| 🌐 **[API Service]({{ '/components/api-service' | relative_url }})** | FastAPI gateway handling HTTP requests and job queuing | `api/` |
| 🎮 **[GPU Workers]({{ '/components/gpu-workers' | relative_url }})** | AI inference engines for LLM and Stable Diffusion | `gpu/` |  
| 📊 **[Monitoring Stack]({{ '/components/monitoring' | relative_url }})** | Observability with Grafana dashboards and metrics | `monitoring/` |

Each component can be:
- **Deployed together** for a complete, integrated solution
- **Deployed separately** across multiple servers for scalability  
- **Mixed and matched** based on your infrastructure requirements

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

### 4. Monitoring Stack (Optional Component)

**Location**: `monitoring/`  
**Deployment**: Independent, can run separately or alongside main application

The monitoring stack is a **standalone component** that provides comprehensive observability across all system components. It can be deployed:

- **Integrated**: Alongside the main application for unified monitoring
- **Centralized**: On a dedicated monitoring server for multiple velesio instances  
- **Development**: Locally for debugging and performance analysis

#### Prometheus
- **Metrics Collection**: System, Redis, GPU, and custom application metrics
- **Alerting**: Configurable alerts for system health and performance  
- **Data Retention**: Configurable retention (default: 200h of metric history)
- **Remote Monitoring**: Can monitor multiple velesio deployments from a central location

#### Grafana
- **Pre-configured Dashboards**: Four auto-provisioned dashboards
  - Redis performance and queue metrics
  - System resources (CPU, memory, disk, network)
  - NVIDIA GPU metrics (utilization, memory, temperature, power)
  - Centralized log viewing and analysis
- **Multi-Instance Support**: Monitor multiple API/GPU worker deployments
- **Alerting**: Visual alerts with multiple notification channels

#### Exporters & Collectors (Auto-deployed)
- **Node Exporter**: System metrics collection
- **Redis Exporter**: Queue and performance metrics  
- **NVIDIA GPU Exporter**: GPU utilization and health metrics
- **Promtail**: Log aggregation from all services

**Deployment Flexibility**: The monitoring stack can be deployed independently from the main application, making it suitable for:
- Multi-environment monitoring (dev, staging, production)
- Cross-datacenter observability  
- Centralized monitoring of distributed velesio deployments

For detailed setup and deployment options, see the [Monitoring Stack Component]({{ '/components/monitoring-stack' | relative_url }}).

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

## Deployment Patterns

velesio AI Server is designed with **component independence** in mind. Each component can be deployed separately or together based on your infrastructure needs:

### 🔗 Monolithic Deployment
Deploy all components on a single server:
```bash
docker-compose up -d  # API + GPU Workers + Redis
cd monitoring && docker-compose up -d  # Optional monitoring
```

### 🔲 Distributed Deployment
Deploy components across multiple servers:

**Server 1 (API + Redis)**:
```bash
# api-only docker-compose.yml
services:
  api:
    # ... API configuration
  redis:
    # ... Redis configuration
```

**Server 2-N (GPU Workers)**:
```bash
# gpu-worker docker-compose.yml
services:
  gpu_worker:
    environment:
      - REMOTE=true
      - REDIS_HOST=server1:6379
```

**Monitoring Server (Optional)**:
```bash
# Central monitoring for all deployments
cd monitoring
# Configure prometheus.yml with remote targets
docker-compose up -d
```

### 🎯 Hybrid Deployment
Mix local and remote components:
- API + Redis locally
- GPU workers on dedicated GPU servers
- Centralized monitoring for multiple environments

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