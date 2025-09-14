# 🚀 Graycat AI Server

High-performance, microservice-based AI inference server with Unity integration support.

[![Deploy on RunPod](https://img.shields.io/badge/Deploy%20on-RunPod-blue?style=for-the-badge)](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55)

## ✨ Features

- **🎯 Unity Ready:** Seamless integration with Unity Assets like "LLM for Unity"
- **⚡ High Performance:** Custom llama.cpp binary with GPU acceleration
- **📈 Scalable:** Redis queue-based worker architecture
- **🐳 Easy Deploy:** Docker Compose setup with auto-downloading models
- **📊 Monitoring:** Built-in Grafana dashboards and observability

## 📚 Documentation

📖 **[Complete Documentation](https://docs.graycat.ai)** - Full guides, API reference, and examples

- 🚀 **[Getting Started](docs/getting-started.md)** - Installation and basic setup
- 🏗️ **[Architecture](docs/architecture.md)** - System design and components  
- 🚢 **[Deployment](docs/deployment.md)** - Production deployment strategies
- 🔌 **[API Reference](docs/api-reference.md)** - Complete endpoint documentation
- 🛠️ **[Components](docs/components.md)** - Individual service configuration
- 🔧 **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## ⚡ Quick Start

### RunPod Template
Deploy instantly on RunPod GPU cloud:
- 🔗 **[One-Click Deploy](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55)**
- Set `REMOTE=false` for standalone inference endpoint (port 1337)
- Set `REMOTE=true` to connect to your Redis queue remotely

### Local Setup
```bash
# 0. Environment:
Linux
NVIDIA GPU with cuda 12.2+ drivers installed
NVIDIA Container Toolkit
Docker compose plugin

# 1. Get the code
git clone https://github.com/GrayCatHQ/graycat-aiserver.git
cd graycat-aiserver

# 2. Setup models and binaries
cd gpu && ./server_setup.sh && cd ..

# 3. Configure environment
cp .env.example .env  # Edit tokens and model URLs

# 4. Launch!
docker-compose up -d

# 5. If you are locally developing you can use the --build flag, and include the undreamai_server binaries in the /gpu dir
docker-compose up -d --build
```

Your API will be available at `http://localhost:8000` 🎉

> 📖 **Need more details?** Check out the **[Getting Started Guide](docs/getting-started.md)** for comprehensive setup instructions.

## 🏗️ Architecture

Distributed microservice design for maximum flexibility:

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

- **API Service:** FastAPI with token auth and job queuing
- **GPU Workers:** Custom llama.cpp + Stable Diffusion inference engines  
- **Redis Queue:** Decoupled job processing for scalability
- **Monitoring:** Pre-configured Grafana dashboards

> 📖 **Learn more:** [Architecture Documentation](docs/architecture.md)

## 🔌 API Endpoints

| Endpoint | Purpose | Documentation |
|----------|---------|---------------|
| `POST /completion` | Unity-compatible text generation | [API Reference](docs/api-reference.md#completion) |
| `POST /generate` | Advanced text generation | [API Reference](docs/api-reference.md#generate) |
| `POST /image` | Stable Diffusion image generation | [API Reference](docs/api-reference.md#image) |
| `GET /health` | Health check (no auth) | [API Reference](docs/api-reference.md#health) |

Authentication: `Authorization: Bearer your-token-here`

## 🎮 Unity Integration

Built specifically for Unity developers:

- **[LLM for Unity](https://assetstore.unity.com/packages/tools/ai-ml-integration/llm-for-unity-273604)** - Recommended Unity asset
- Compatible `/completion` endpoint for seamless integration
- Base64 image encoding for Stable Diffusion support

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Questions?** Check the [Documentation](docs/) or open an issue!
