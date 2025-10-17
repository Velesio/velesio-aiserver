---
layout: home
title: Home
nav_order: 1
---

# Velesio AI Server

A high-performance, microservice-based AI inference server designed for scalable LLM and Stable Diffusion workloads.

## Overview

Velesio AI Server is a production-ready AI inference platform that provides:

- **LLM Text Generation** via custom llama.cpp integration
- **Stable Diffusion Image Generation** with WebUI support
- **Redis Queue Architecture** for scalable job processing
- **Docker-based Deployment** with GPU acceleration
- **Built-in Monitoring** with Grafana and Prometheus
- **Unity Integration** ready endpoints

## Architecture

```
┌─────────────┐    ┌─────────┐    ┌─────────────┐
│    API      │────│  Redis  │────│ GPU Workers │
│  (FastAPI)  │    │ Queue   │    │ (LLM + SD)  │
└─────────────┘    └─────────┘    └─────────────┘
       │                                  │
       │           ┌─────────────┐        │
       └───────────│ Monitoring  │────────┘
                   │(Grafana+Prom)│
                   └─────────────┘
```

## Key Features

### 🚀 **High Performance**
- Custom llama.cpp binary (`undreamai_server`) for optimized inference
- GPU acceleration with CUDA support
- Asynchronous job processing via Redis Queue

### 🔧 **Easy Setup**
- Docker Compose deployment
- Automatic model downloading
- Pre-configured monitoring stack

### 🎯 **Unity Ready**
- Compatible with "LLM for Unity" asset
- Base64 image encoding for seamless integration
- Standardized API endpoints

### 📊 **Production Monitoring**
- Real-time metrics with Prometheus
- Visual dashboards in Grafana
- Redis queue monitoring
- GPU utilization tracking

## Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | FastAPI web server |
| Redis | 6379 | Message queue |
| LLM Worker | 1337 | Direct LLM access (when REMOTE=false) |
| Stable Diffusion | 7860 | WebUI interface (when RUN_SD=true) |
| Grafana | 3000 | Monitoring dashboard |
| Prometheus | 9090 | Metrics collection |

## Next Steps

- [Quickstart Cloud Infra](quickstart-runpod.html) - Detailed setup instructions
- [Quickstart Self hosted](quickstart-selfhost.html) - Deep dive into system design
- [Architecture](architecture.html) - Complete endpoint documentation
- [Deployment Guide](deployment.html) - Production deployment strategies
- [Model Templates](model-templates.html) - Common issues and solutions

---

**Need help?** Check our [troubleshooting guide](troubleshooting.html) or open an issue on [GitHub](https://github.com/Velesio/Velesio-aiserver).