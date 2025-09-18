---
layout: page
title: Components
nav_order: 4
has_children: true
---

# Components

neovratz AI Server is built with a **modular, component-based architecture** where each component can be deployed independently or together based on your infrastructure needs.

## Available Components

<div class="component-grid">
  <div class="component-card">
    <div class="component-header">
      <h3>🌐 API Service</h3>
      <span class="component-location">api/</span>
    </div>
    <p class="component-description">
      FastAPI-based web server that handles HTTP requests, authentication, and job queuing to GPU workers.
    </p>
    <div class="component-features">
      <span class="feature-tag">FastAPI</span>
      <span class="feature-tag">Authentication</span>
      <span class="feature-tag">Job Queuing</span>
    </div>
    <a href="{{ '/components/api-service' | relative_url }}" class="component-link">View Documentation →</a>
  </div>

  <div class="component-card">
    <div class="component-header">
      <h3>🎮 GPU Workers</h3>
      <span class="component-location">gpu/</span>
    </div>
    <p class="component-description">
      Specialized containers that handle AI inference tasks using NVIDIA GPUs for both LLM and Stable Diffusion workloads.
    </p>
    <div class="component-features">
      <span class="feature-tag">CUDA</span>
      <span class="feature-tag">LLM Inference</span>
      <span class="feature-tag">Stable Diffusion</span>
    </div>
    <a href="{{ '/components/gpu-workers' | relative_url }}" class="component-link">View Documentation →</a>
  </div>

  <div class="component-card">
    <div class="component-header">
      <h3>📊 Monitoring Stack</h3>
      <span class="component-location">monitoring/</span>
    </div>
    <p class="component-description">
      Comprehensive observability solution with Grafana dashboards, Prometheus metrics, and centralized logging.
    </p>
    <div class="component-features">
      <span class="feature-tag">Grafana</span>
      <span class="feature-tag">Prometheus</span>
      <span class="feature-tag">Observability</span>
    </div>
    <a href="{{ '/components/monitoring' | relative_url }}" class="component-link">View Documentation →</a>
  </div>
</div>

## Deployment Flexibility

Each component can be deployed in multiple ways:

### 🏢 **All-in-One Deployment**
Deploy all components on a single server for a complete, integrated solution:
```bash
docker-compose up -d                    # API + GPU Workers + Redis
cd monitoring && docker-compose up -d   # Optional monitoring
```

### 🌐 **Distributed Deployment**
Deploy components across multiple servers for scalability:
```bash
# Server 1: API + Redis
docker-compose -f docker-compose.api.yml up -d

# Server 2-N: GPU Workers
docker-compose -f docker-compose.gpu.yml up -d

# Monitoring Server: Centralized observability
cd monitoring && docker-compose up -d
```

### 🎯 **Component-Specific Deployment**
Deploy only the components you need:
- **API-only**: For serverless GPU workers or external inference services
- **GPU-only**: For dedicated inference workers connecting to remote APIs  
- **Monitoring-only**: For centralized observability across multiple deployments

## Component Communication

```
┌─────────────┐    ┌─────────┐    ┌─────────────┐
│ API Service │────│  Redis  │────│ GPU Workers │
│  (FastAPI)  │    │ Queue   │    │ (LLM + SD)  │
└─────────────┘    └─────────┘    └─────────────┘
       │                                  │
       │           ┌─────────────┐        │
       └───────────│ Monitoring  │────────┘
                   │   Stack     │
                   └─────────────┘
```

- **API Service** receives HTTP requests and queues jobs
- **Redis** serves as the message broker between API and workers
- **GPU Workers** pull jobs from the queue and process AI inference
- **Monitoring Stack** observes all components and provides metrics/alerts

Each component is designed to be:
- **Independently deployable**
- **Horizontally scalable** 
- **Self-contained** with minimal dependencies
- **Observable** through the monitoring stack

<style>
.component-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.component-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.component-card:hover {
  border-color: var(--link-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.component-header h3 {
  margin: 0;
  color: var(--text-color);
  font-size: 1.2rem;
}

.component-location {
  background-color: var(--bg-tertiary);
  color: var(--text-muted);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: monospace;
}

.component-description {
  color: var(--text-secondary);
  margin-bottom: 1rem;
  line-height: 1.5;
}

.component-features {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.feature-tag {
  background-color: var(--bg-tertiary);
  color: var(--text-color);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  border: 1px solid var(--border-color);
}

.component-link {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.component-link:hover {
  color: var(--link-hover);
}

@media (max-width: 768px) {
  .component-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .component-card {
    padding: 1rem;
  }
}
</style>