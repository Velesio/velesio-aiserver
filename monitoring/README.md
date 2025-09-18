# Monitoring Stack

This monitoring setup provides comprehensive observability for the neovratz-aiserver with pre-configured dashboards.

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards with auto-provisioned dashboards
- **Redis Exporter**: Exports Redis metrics to Prometheus
- **Node Exporter**: Exports system metrics to Prometheus
- **NVIDIA GPU Exporter**: Exports GPU metrics including utilization, memory, temperature, and power consumption

## Pre-configured Dashboards

The following dashboards are automatically provisioned on startup:

- **Redis Dashboard** (ID: 14091): Comprehensive Redis monitoring including memory usage, commands, connections, and performance metrics
- **Node Exporter Full** (ID: 1860): Complete system resource monitoring including CPU, memory, disk, network, and system stats
- **NVIDIA GPU Metrics** (ID: 14574): GPU monitoring including utilization, memory usage, temperature, power draw, fan speed, and clock speeds

## Quick Start

1. Make sure your main Redis instance is running (the one used by neovratz-aiserver)

2. Set the Redis password environment variable to match your main Redis instance:
```bash
export REDIS_PASS="your_actual_redis_password"
```

3. Start the monitoring stack:
```bash
cd monitoring
docker-compose up -d
```

4. Access services:
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **Prometheus**: http://localhost:9090
   - **Redis Exporter**: http://localhost:9121
   - **Node Exporter**: http://localhost:9100

## Configuration

The dashboards are automatically loaded from `/grafana/dashboards/` directory. The setup includes:

- Prometheus scraping configuration for all exporters
- Grafana data source auto-configuration
- Dashboard auto-provisioning
- Persistent volumes for data retention

## Troubleshooting

### Redis Metrics
If Redis metrics aren't showing:
1. Verify Redis is accessible from Docker containers
2. Check the REDIS_PASS environment variable matches your Redis password
3. Ensure Redis is listening on the expected port (6379)

### GPU Metrics  
If GPU metrics aren't showing:
1. Ensure NVIDIA drivers are installed on the host system
2. Verify Docker has access to GPU devices (`docker run --gpus all nvidia/cuda nvidia-smi`)
3. Check that `/dev/nvidia*` devices exist on the host
4. Ensure `nvidia-smi` command works on the host system
5. For multiple GPUs, add additional device mappings in docker-compose.yaml:
   ```yaml
   devices:
     - /dev/nvidiactl:/dev/nvidiactl
     - /dev/nvidia0:/dev/nvidia0
     - /dev/nvidia1:/dev/nvidia1  # Add for each GPU
     - /dev/nvidia-uvm:/dev/nvidia-uvm
   ``` Stack Setup

This directory contains a complete monitoring stack with Grafana, Prometheus, Node Exporter, and Redis monitoring.

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Node Exporter**: System metrics (CPU, memory, disk, network)
- **Redis Exporter**: Redis instance monitoring

## Prerequisites

- Docker and Docker Compose installed
- Redis instance running on localhost:6379

## Quick Start

1. Start the monitoring stack:
   ```bash
   docker-compose up -d
   ```

2. Access the services:
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **Prometheus**: http://localhost:9090
   - **Node Exporter**: http://localhost:9100/metrics
   - **Redis Exporter**: http://localhost:9121/metrics

## Configuration

### Grafana
- Default credentials: admin/admin (change on first login)
- Prometheus is automatically configured as a data source
- Pre-configured dashboard for system and Redis monitoring

### Prometheus
- Scrapes metrics every 15 seconds
- Configured targets:
  - Self-monitoring (Prometheus)
  - Node Exporter (system metrics)
  - Redis Exporter (Redis metrics)

### Redis Monitoring
The Redis exporter connects to Redis at `localhost:6379`. If your Redis instance runs on a different host or port, update the `REDIS_ADDR` environment variable in `docker-compose.yaml`.

## Customization

### Adding More Targets
Edit `prometheus.yml` to add more scrape targets:

```yaml
scrape_configs:
  - job_name: 'my-app'
    static_configs:
      - targets: ['my-app:8080']
```

### Custom Dashboards
Add JSON dashboard files to `grafana/dashboards/` directory. They will be automatically loaded.

### Alerts
Create alert rules in `prometheus.yml` under the `rule_files` section.

## Troubleshooting

1. **Redis connection issues**: Check if Redis is running and accessible
2. **Permission issues**: Ensure Docker has access to system paths
3. **Port conflicts**: Change port mappings in docker-compose.yaml if needed

## Stopping the Stack

```bash
docker-compose down
```

To also remove volumes (will delete all data):
```bash
docker-compose down -v
```
