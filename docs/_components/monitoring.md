---
layout: page
title: Monitoring Stack
parent: Components
nav_order: 3
---

# Monitoring Stack

A comprehensive observability solution that provides real-time monitoring, metrics collection, and alerting for all Velesio AI Server components.

## Overview

**Location**: `monitoring/`  
**Technology**: Grafana + Prometheus + Exporters  
**Container**: `monitoring-stack`  
**Ports**: 3000 (Grafana), 9090 (Prometheus)

The monitoring stack is a **standalone, optional component** that can be deployed:
- **Alongside** the main application for integrated monitoring
- **Separately** for external monitoring of multiple Velesio deployments  
- **Independently** for development and testing environments

## Deployment Flexibility

### 🔗 Integrated Deployment
Deploy with the main application for seamless monitoring:
```bash
# Start main application
docker-compose up -d

# Start monitoring stack
cd monitoring
docker-compose up -d
```

### 🔲 Standalone Deployment  
Deploy monitoring independently on a dedicated monitoring server:
```bash
# On monitoring server
git clone https://github.com/Velesio/Velesio-aiserver.git
cd Velesio-aiserver/monitoring

# Configure remote targets in prometheus.yml
docker-compose up -d
```

### 🎯 Selective Monitoring
Monitor only specific components by configuring Prometheus targets:
```yaml
# Monitor only API service
- job_name: 'Velesio-api'
  static_configs:
    - targets: ['remote-host:8000']
```

## Overview

The monitoring stack provides real-time insights into:
- **System Performance**: CPU, memory, disk, and network utilization
- **GPU Metrics**: NVIDIA GPU utilization, memory, temperature, and power consumption
- **Redis Performance**: Queue depth, memory usage, connections, and command statistics
- **Application Logs**: Centralized log aggregation and analysis
- **Container Metrics**: Docker container resource usage and health

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Exporters  │────│ Prometheus  │────│   Grafana   │
│ (Metrics)   │    │ (Storage)   │    │ (Dashboard) │
└─────────────┘    └─────────────┘    └─────────────┘
       │                                      │
       │           ┌─────────────┐            │
       └───────────│    Loki     │────────────┘
                   │(Log Storage)│
                   └─────────────┘
                          │
                   ┌─────────────┐
                   │  Promtail   │
                   │(Log Collect)│
                   └─────────────┘
```

## Components

### Core Services

| Service | Port | Purpose |
|---------|------|---------|
| **Grafana** | 3000 | Visualization dashboards and alerts |
| **Prometheus** | 9090 | Metrics collection and time-series storage |
| **Loki** | 3100 | Log aggregation and storage |
| **Promtail** | - | Log collection agent |

### Exporters

| Exporter | Port | Metrics |
|----------|------|---------|
| **Node Exporter** | 9100 | System metrics (CPU, memory, disk, network) |
| **Redis Exporter** | 9121 | Redis performance and queue metrics |
| **NVIDIA GPU Exporter** | 9835 | GPU utilization, memory, temperature, power |

## Pre-configured Dashboards

The monitoring stack includes four auto-provisioned dashboards:

### 🖥️ Node Exporter Full
- **CPU utilization** and load averages
- **Memory usage** and swap statistics
- **Disk I/O** and filesystem usage
- **Network traffic** and interface statistics
- **System uptime** and process counts

### 📊 Redis Dashboard
- **Memory usage** and keyspace statistics
- **Command execution** rates and latency
- **Client connections** and blocked clients
- **Replication** status and lag
- **Queue depth** monitoring for job processing

### 🎮 NVIDIA GPU Metrics
- **GPU utilization** percentage
- **Memory usage** and allocation
- **Temperature** monitoring
- **Power consumption** and limits
- **Fan speed** and clock frequencies

### 📝 Velesio Logs
- **Centralized log viewing** from all services
- **Log level filtering** (INFO, WARNING, ERROR)
- **Search and filtering** capabilities
- **Real-time log streaming**

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- NVIDIA drivers (for GPU monitoring)
- Running Velesio AI Server instance

### Setup

1. **Configure Redis connection** (if using external Redis):
   ```bash
   cd monitoring
   cp .env.example .env
   # Edit .env with your Redis connection details
   ```

2. **Start monitoring stack**:
   ```bash
   cd monitoring
   docker-compose up -d
   ```

3. **Access Grafana**:
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin`

### For GPU Monitoring

Enable GPU monitoring by starting with the GPU profile:
```bash
docker-compose --profile gpu up -d
```

## Configuration

### Environment Variables

```bash
# Redis connection (optional, defaults to localhost)
REDIS_HOST=localhost:6379
REDIS_PASS=your_redis_password
```

### Dashboard Customization

Dashboards are automatically loaded from `grafana/dashboards/`. To add custom dashboards:

1. Export dashboard JSON from Grafana
2. Place JSON file in `monitoring/grafana/dashboards/`
3. Restart Grafana: `docker-compose restart grafana`

### Retention Settings

Data retention can be configured in `prometheus.yml`:
```yaml
command:
  - '--storage.tsdb.retention.time=200h'  # Adjust as needed
```

## Usage

### Monitoring Velesio AI Server

1. **API Performance**: Monitor request rates and response times
2. **Queue Health**: Check Redis queue depth and processing rates
3. **GPU Utilization**: Track inference workload and memory usage
4. **System Resources**: Ensure adequate CPU, memory, and disk space

### Alert Setup

Configure alerts in Grafana for:
- High GPU memory usage (>90%)
- Redis queue backlog (>1000 jobs)
- High system load (>80%)
- Disk space usage (>85%)

### Log Analysis

Use the Velesio Logs dashboard to:
- Debug API request failures
- Monitor worker job processing
- Track model loading times
- Investigate performance issues

## Troubleshooting

### Common Issues

**Grafana not loading dashboards**:
```bash
# Check dashboard provisioning
docker logs grafana
# Restart with clean data
docker-compose down -v && docker-compose up -d
```

**GPU metrics not appearing**:
```bash
# Verify NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
# Check exporter logs
docker logs nvidia-gpu-exporter
```

**Redis connection failed**:
```bash
# Verify Redis accessibility
docker exec redis-exporter redis-cli -h $REDIS_HOST ping
# Check network connectivity
docker-compose logs redis-exporter
```

### Performance Tuning

For high-volume environments:

1. **Increase scrape intervals** in `prometheus.yml`
2. **Adjust retention periods** based on storage capacity
3. **Configure log rotation** for Loki
4. **Set resource limits** in Docker Compose

## Integration

### With Main Application

The monitoring stack is designed to work alongside the main Velesio AI Server:

```bash
# Start main application
docker-compose up -d

# Start monitoring in separate terminal
cd monitoring
docker-compose up -d
```

### Custom Metrics

Add application-specific metrics by:

1. Exposing metrics endpoint in your service
2. Adding scrape config to `prometheus.yml`
3. Creating custom Grafana dashboard

## Security

### Production Deployment

For production use:

1. **Change default credentials**:
   ```yaml
   environment:
     - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
   ```

2. **Enable HTTPS** with reverse proxy
3. **Restrict network access** to monitoring ports
4. **Configure authentication** (LDAP, OAuth, etc.)

## Maintenance

### Backup

Important data to backup:
- Grafana dashboards: `grafana_data:/var/lib/grafana`
- Prometheus data: `prometheus_data:/prometheus`
- Configuration files: `monitoring/`

### Updates

Update to latest versions:
```bash
docker-compose pull
docker-compose up -d
```

## Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Node Exporter Metrics](https://github.com/prometheus/node_exporter)
- [Redis Exporter Metrics](https://github.com/oliver006/redis_exporter)