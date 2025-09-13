---
layout: page
title: Deployment
nav_order: 5
---

# Deployment Guide

This guide covers production deployment strategies for Graycat AI Server's independent components.

## Component Deployment Options

Graycat AI Server is built with **modular components** that can be deployed flexibly:

### 🏢 All-in-One Deployment
Deploy all components on a single server:
```bash
# Complete stack on one machine
docker-compose up -d                    # API + GPU Workers + Redis
cd monitoring && docker-compose up -d   # Optional monitoring
```

### 🌐 Distributed Deployment  
Deploy components across multiple servers:
```bash
# Server 1: API + Redis
docker-compose -f docker-compose.api.yml up -d

# Server 2-N: GPU Workers (connect to remote Redis)
docker-compose -f docker-compose.gpu.yml up -d

# Monitoring Server: Centralized observability
cd monitoring && docker-compose up -d
```

### 🎯 Component-Specific Deployment
Deploy only the components you need:
- **API-only**: For serverless GPU workers or external inference services
- **GPU-only**: For dedicated inference workers connecting to remote APIs
- **Monitoring-only**: For centralized observability across multiple deployments

See individual component documentation: [API Service]({{ '/components/api-service' | relative_url }}), [GPU Workers]({{ '/components/gpu-workers' | relative_url }}), [Monitoring Stack]({{ '/components/monitoring-stack' | relative_url }})

## Production Architecture

For production environments, consider this architecture:

```
Internet
    │
    ▼
┌───────────────┐
│ Load Balancer │  (AWS ALB, Cloudflare, nginx)
│   (SSL/TLS)   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  API Gateway  │  (Multiple instances)
│   (FastAPI)   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│     Redis     │  (Managed Redis or cluster)
│   (Cluster)   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ GPU Workers   │  (Auto-scaling group)
│ (LLM + SD)    │
└───────────────┘
```

## Deployment Options

### 1. Single Server Deployment

**Best for**: Development, small teams, low-traffic applications

**Requirements**:
- 1 server with GPU (NVIDIA RTX 3080+ or A100)
- 16GB+ RAM
- 100GB+ SSD storage
- Docker with NVIDIA runtime

**Setup**:
```bash
# 1. Clone repository
git clone https://github.com/GrayCatHQ/graycat-aiserver.git
cd graycat-aiserver

# 2. Configure production environment
cp .env.example .env.production
nano .env.production

# 3. Use production compose file
docker-compose -f docker-compose.prod.yml up -d --build
```

### 2. Multi-Server Deployment

**Best for**: High availability, horizontal scaling

**Architecture**:
- **API Servers**: 2+ instances behind load balancer
- **Redis Cluster**: 3+ nodes for high availability  
- **GPU Workers**: Scalable worker pool
- **Monitoring**: Centralized metrics collection

### 3. Cloud Deployment

#### AWS Deployment

**Services Used**:
- **ECS/EKS**: Container orchestration
- **ALB**: Application Load Balancer
- **ElastiCache**: Managed Redis
- **EC2 GPU Instances**: p3/p4 instances for workers
- **CloudWatch**: Monitoring and logging

**Example ECS Task Definition**:
```json
{
  "family": "graycat-api",
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "graycathq/graycat-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "REDIS_URL",
          "value": "redis://your-elasticache-cluster:6379"
        }
      ]
    }
  ]
}
```

#### Google Cloud Platform

**Services Used**:
- **GKE**: Kubernetes clusters with GPU nodes
- **Cloud Load Balancing**: HTTP(S) load balancer
- **Memorystore**: Managed Redis
- **Compute Engine**: GPU-enabled VMs

#### Azure Deployment

**Services Used**:
- **AKS**: Azure Kubernetes Service
- **Application Gateway**: Load balancer
- **Azure Cache for Redis**: Managed Redis
- **Virtual Machines**: GPU-enabled instances

## Docker Production Configuration

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    build: ./api
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379
      - API_TOKENS=${API_TOKENS}
      - LOG_LEVEL=INFO
    depends_on:
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 1gb
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 1G

  gpu_worker:
    build: ./gpu
    restart: unless-stopped
    runtime: nvidia
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - GPU_LAYERS=35
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./gpu/data:/app/data
    depends_on:
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  redis_data:
```

### Nginx Configuration

Create `nginx/nginx.prod.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server api:8000;
        # Add more API instances for load balancing
        # server api-2:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API proxy
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeout settings
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;

            # Buffer settings for large responses
            proxy_buffering on;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
        }

        # Health check endpoint
        location /health {
            access_log off;
            proxy_pass http://api_backend;
        }
    }
}
```

## Environment Configuration

### Production Environment Variables

```bash
# .env.production

# API Configuration
API_TOKENS=prod-token-1,prod-token-2,prod-token-3
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-app.com,https://api.your-app.com

# Redis Configuration (for remote Redis)
REDIS_URL=redis://your-redis-cluster:6379
REDIS_PASSWORD=your-redis-password

# GPU Worker Configuration
GPU_LAYERS=35
CUDA_VISIBLE_DEVICES=0
MODEL_CACHE_SIZE=2

# Model URLs (for auto-download)
MODEL_URL=https://huggingface.co/your-org/model/resolve/main/model.gguf
SD_MODEL_URL=https://huggingface.co/your-org/sd-model/resolve/main/model.safetensors

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=secure-password

# Security
RATE_LIMIT_PER_MINUTE=100
MAX_CONCURRENT_REQUESTS=50
```

## Security Considerations

### 1. API Security

**Authentication**:
- Use strong, randomly generated API tokens
- Rotate tokens regularly
- Implement token scoping for different access levels

**Rate Limiting**:
```nginx
# In nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req zone=api burst=50 nodelay;
```

**Input Validation**:
- All inputs validated with Pydantic models
- Prompt length limits to prevent abuse
- File upload restrictions for image endpoints

### 2. Network Security

**Firewall Rules**:
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw deny 6379   # Redis (internal only)
ufw deny 8000   # API (behind nginx)
```

**TLS Configuration**:
- Use Let's Encrypt for free SSL certificates
- Implement HSTS headers
- Use modern TLS protocols only

### 3. Container Security

**Docker Security**:
```yaml
# In docker-compose.prod.yml
services:
  api:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"  # Non-root user
```

## Monitoring and Logging

Graycat AI Server includes a comprehensive monitoring stack with Grafana dashboards, Prometheus metrics, and centralized logging. For complete setup instructions and usage details, see the [Monitoring Documentation]({{ '/components/monitoring' | relative_url }}).

### Production Monitoring Stack

```yaml
# monitoring/docker-compose.prod.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.prod.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_SMTP_ENABLED=true
      - GF_SMTP_HOST=smtp.gmail.com:587
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - loki_data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

### Log Management

**Structured Logging**:
```python
# In FastAPI application
import structlog

logger = structlog.get_logger()

@app.post("/completion")
async def completion(request: CompletionRequest):
    logger.info("completion_request", 
                prompt_length=len(request.prompt),
                max_tokens=request.max_tokens)
```

**Log Rotation**:
```bash
# /etc/logrotate.d/graycat
/var/log/graycat/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker kill -s USR1 $(docker ps -q --filter name=graycat)
    endscript
}
```

## Scaling Strategies

### Horizontal Scaling

**API Scaling**:
```bash
# Scale API instances
docker-compose -f docker-compose.prod.yml up -d --scale api=4
```

**GPU Worker Scaling**:
```bash
# Scale GPU workers across multiple machines
# Machine 1
CUDA_VISIBLE_DEVICES=0,1 docker-compose up gpu_worker

# Machine 2  
CUDA_VISIBLE_DEVICES=0,1 docker-compose up gpu_worker
```

### Auto-scaling with Kubernetes

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: graycat-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: graycat-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: queue_depth
      target:
        type: AverageValue
        averageValue: "5"
```

## Backup and Recovery

### Data Backup

**Redis Backup**:
```bash
# Daily Redis backup
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb /backups/redis_${DATE}.rdb
```

**Model Backup**:
```bash
# Sync models to S3
aws s3 sync ./gpu/data/models s3://your-bucket/models --delete
```

### Disaster Recovery

**Recovery Plan**:
1. Restore Redis from latest backup
2. Deploy containers from Docker images
3. Download models from backup location
4. Verify health checks pass
5. Update DNS to point to new infrastructure

## Performance Optimization

### GPU Optimization

**Model Quantization**:
- Use GGUF format with appropriate quantization (Q4_K_M, Q5_K_M)
- Balance model size vs. quality based on requirements

**Memory Management**:
```bash
# Optimize GPU memory usage
export CUDA_MEMORY_FRACTION=0.9
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### API Optimization

**Caching**:
```python
# Redis-based response caching
@app.post("/completion")
@cache(expire=3600)  # Cache for 1 hour
async def completion(request: CompletionRequest):
    # Implementation
```

**Connection Pooling**:
```python
# Redis connection pool
redis_pool = redis.ConnectionPool(
    host='redis', 
    port=6379, 
    max_connections=100
)
```

## Troubleshooting Production Issues

### Common Issues

**High Queue Depth**:
- Scale GPU workers
- Optimize model inference speed
- Implement request queuing limits

**Memory Issues**:
- Monitor GPU memory usage
- Reduce model context length
- Implement model unloading

**API Timeouts**:
- Increase nginx timeout settings
- Optimize database queries
- Implement circuit breakers

### Monitoring Alerts

**Grafana Alerts**:
```yaml
# alerts.yml
groups:
- name: graycat
  rules:
  - alert: HighQueueDepth
    expr: redis_queue_depth > 10
    for: 5m
    annotations:
      summary: "High queue depth detected"
      
  - alert: GPUMemoryHigh
    expr: nvidia_gpu_memory_used_percent > 90
    for: 2m
    annotations:
      summary: "GPU memory usage critical"
```

## Next Steps

- [API Reference](api-reference.html) - Complete API documentation
- [Troubleshooting](troubleshooting.html) - Common issues and solutions
- [Architecture](architecture.html) - System design details