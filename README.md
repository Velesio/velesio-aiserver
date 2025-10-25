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

- 🚀 **[Cloud Quickstart](docs/quickstart-runpod.md)** - Get started quickly with Runpod!
- 🚀 **[Self Hosted Quickstart](docs/quickstart-selfhost.md)** - Get started with your own infrastructure!

### RunPod
Deploy instantly on RunPod GPU cloud:
- 🔗 **[One-Click Deploy of GPU component](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55)**
- Set `API=false` for standalone inference endpoint (make sure to expose llamacpp and SD ports)
- Set `API=true` to connect to API Redis queue from API component

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
docker compose up -d

# If you are locally developing you can use the --build flag, and include the undreamai_server binaries in the /gpu dir with the server_setup.sh script
docker compose up -d --build

# There is also an included grafana monitoring stack!
cd monitoring
docker compose up -d
```

Your API will be available at `http://localhost:8000` 🎉

## 🎮 Unity Integrations

Built specifically for Unity developers:

- **[LLM for Unity](https://assetstore.unity.com/packages/tools/ai-ml-integration/llm-for-unity-273604)** - Text Generation
- **[SD Integration For Untiy](https://github.com/dobrado76/Stable-Diffusion-Unity-Integration)** - Image Generation

## 📚 Documentation

📖 **[Complete Documentation](https://velesio.github.io/velesio-aiserver/)** - Full guides, API reference, and examples

- 🏗️ **[Model Templates](docs/model-templates.md)** - Model stack templates
- 🚢 **[Deployment Strategies](docs/model-templates.md)** - Both distributed and standalone
- 🛠️ **[Components](docs/model-templates.md)** - Individual service configuration
- 🎮 **[Discord](https://discord.gg/3WgaZqCq)** - For Support & Discussion

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
