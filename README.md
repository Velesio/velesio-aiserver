# Hardware
`This setup assumes you are running a NVIDIA GPU with CUDA support.`

## Quick Start

0. Download the undreamai_server binaries
```bash
cd gpu
./server_setup.sh
```

1. Set environment variables in a .env file:
```bash
REDIS_PASS="your_secure_password"
API_TOKENS="your-secret-token-here"
```

2. Build image and start services:
```bash
docker-compose up -d --build
```

## Architecture

- **API Server** (`api/`): FastAPI service with authentication, queues inference jobs to Redis
- **GPU Worker** (`gpu/`): Processes LLM inference using CUDA-enabled llama.cpp server
- **Redis**: Job queue and message broker between API and workers
- **Monitoring** (`monitoring/`): Prometheus + Grafana stack for observability
- **RunPod Controller** (`runpod-controller/`): Auto-scaling script for cloud GPU instances

## Endpoints

- `Authentication is through a Bearer token`
- `/docs` for API documentation
- `POST /generate` - Queue text generation
- `POST /completion` - Unity-compatible completion API
- `POST /template` - Get chat template
- `POST /tokenize` - Tokenize text
- `GET /health` - Health check (no auth required)

## Additional Features`

- **Authentication**: Secure API access with Bearer tokens stored in Postgres
- **Frontend**: User-friendly interface with secure login, creating an api key and credits
- **Stable Diffusion Integration**: Host Automatic 1111 SD server with /gpu and use it with [this Unity Asset](https://github.com/dobrado76/Stable-Diffusion-Unity-Integration)