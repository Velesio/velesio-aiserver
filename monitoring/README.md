# Monitoring Stack Setup

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
