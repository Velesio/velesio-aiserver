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

- 🚀 **[RunPod Quickstart](docs/quickstart-runpod.md)** - Get started quickly with Runpod! New to RunPod? [Use my refferal link](https://runpod.io?ref=muhg2w55) to get a 5$ bonus and support the project!

- 🚀 **[Self Hosted Quickstart](docs/quickstart-selfhost.md)** - Get started with your own infrastructure!

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
