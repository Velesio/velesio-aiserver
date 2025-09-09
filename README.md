# Hardware
`This setup assumes you are running a NVIDIA GPU with CUDA support.`

## Quick Start

0. Download the undreamai_server binaries and make sure you have a model in /gpu/models, the MODEL_URL will wget a model if you do not.
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

- **GPU Worker** (`gpu/`): LLM inference using CUDA-enabled undreamai(llmacpp customized for unity) server, locally or connecting to a remote API Server through Redis Queue
- **API Server** (`api/`): FastAPI service with authentication, queues inference jobs to Redis
- **Redis**: Job queue and message broker between API and workers
- **Nginx**: Reverse proxy for secure remote hosting
- **Monitoring** (`monitoring/`): Grafana stack and templates for observability; By default brings up Redis and Node Exporter dashboards

## Endpoints

- `Authentication is through a Bearer token`
- `/docs` for API documentation
- `POST /generate` - Queue text generation
- `POST /completion` - Unity-compatible completion API
- `POST /template` - Get chat template
- `POST /tokenize` - Tokenize text
- `GET /health` - Health check (no auth required)

## Unity Integration Links
- `[Undream LLM for Unity](https://assetstore.unity.com/packages/tools/ai-ml-integration/llm-for-unity-273604)
- `[dobrado76 Stable Diffusion Unity Integration](https://github.com/dobrado76/Stable-Diffusion-Unity-Integration/discussions)
