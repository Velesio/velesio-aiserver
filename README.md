# 🚀 Velesio AI Server

High-performance, microservice-based AI inference server with Unity integration support.

[![Deploy on RunPod](https://img.shields.io/badge/Deploy%20on-RunPod-blue?style=for-the-badge)](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55)

## ✨ Features

- **🎯 Unity Ready:** Seamless integration with Unity Assets like "LLM for Unity"
- **⚡ High Performance:** Custom llama.cpp binary with GPU acceleration
- **📈 Scalable:** Redis queue-based worker architecture
- **🐳 Easy Deploy:** Docker Compose setup with auto-downloading models
- **📊 Monitoring:** Built-in Grafana dashboards and observability

## ⚡ Quick Start

### RunPod Template
Deploy instantly on RunPod GPU cloud:
- 🔗 **[One-Click Deploy of GPU component](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55)**
- Set `REMOTE=false` for standalone inference endpoint (make sure to expose llamacpp and SD ports)
- Set `REMOTE=true` to connect to remote Redis queue from API component

### Local Setup
```bash
# 0. Environment:
Linux
NVIDIA GPU with cuda 12.2+ drivers installed
NVIDIA Container Toolkit
Docker compose plugin

# 1. Get the code
git clone https://github.com/velesio/velesio-aiserver.git
cd velesio-aiserver

# 2. Configure environment
cp .env.example .env  # Edit tokens and model URLs

# 3. Launch!
docker-compose up -d

# 4. If you are locally developing you can use the --build flag, and include the undreamai_server binaries in the /gpu dir with the server_setup.sh script
docker-compose up -d --build
```

Your API will be available at `http://localhost:8000` 🎉

> 📖 **Need more details?** Check out the **[Getting Started Guide](docs/getting-started.md)** for comprehensive setup instructions.

## 🎮 Unity Integrations

Built specifically for Unity developers:

- **[LLM for Unity](https://assetstore.unity.com/packages/tools/ai-ml-integration/llm-for-unity-273604)** - Text Generation
- **[SD Integration For Untiy](https://github.com/dobrado76/Stable-Diffusion-Unity-Integration)** - Image Generation

## 📚 Documentation

📖 **[Complete Documentation](https://velesio.github.io/velesio-aiserver/)** - Full guides, API reference, and examples

- 🚀 **[Getting Started](docs/getting-started.md)** - Installation and basic setup
- 🏗️ **[Architecture](docs/architecture.md)** - System design and components  
- 🚢 **[Deployment](docs/deployment.md)** - Production deployment strategies
- 🔌 **[API Reference](docs/api-reference.md)** - Complete endpoint documentation
- 🛠️ **[Components](docs/components.md)** - Individual service configuration
- 🔧 **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

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

---

## 🔌 Open Source References
[UndreamAI UnityAsset and Server](https://github.com/undreamai)
[dobrado76 SD Integration for Unity](https://github.com/dobrado76/Stable-Diffusion-Unity-Integration)
[Automatic1111 SD Web server](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
[LLAMACPP](https://github.com/ggml-org/llama.cpp)

**Questions?** Check the [Documentation](docs/) or open an issue!
