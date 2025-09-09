# 🚀 Graycat AI Server 🚀

Your self-hosted AI powerhouse for Unity and beyond. Blazing fast, fully customizable, and ready to roll.

---
## [Runpod Template Quickstart](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55)
*   **REMOTE: false** False hosts the LLAMACPP endpoint on the exposed port (1337 by default.)
*   **REMOTE: true** Connects to remote API Server's redis queue. In that case you do not need to expose any ports. It is Reccomended to have a Firewall on your API Server's end and only allow the GPU worker IPs on the Redis port.

---

## ✨ Features

*   **High-Speed Inference:** Leverages NVIDIA GPUs with CUDA for maximum performance.
*   **Unity Ready:** Seamless integration with the Undream LLM asset for Unity.
*   **Scalable:** Built with Docker and a worker-queue architecture to handle any load.
*   **Secure:** Token-based authentication for your API endpoints.
*   **Observable:** Comes with a Grafana monitoring stack to keep an eye on everything.

---

## 🏁 Get Started in Minutes

Get your server running with just a few commands.

**Prerequisites:**
*   NVIDIA GPU with CUDA support.
*   Docker & Docker Compose.

**1. Initial Setup**

First, grab the `undreamai_server` binaries and make sure you have a model in `/gpu/models`. The `MODEL_URL` in `server_setup.sh` will fetch one for you if the directory is empty.

```bash
cd gpu
./server_setup.sh
```

**2. Configure Your Environment**

Create a `.env` file in the root directory and add your secrets.

```bash
# .env
REDIS_PASS="your_secure_password"
API_TOKENS="your-secret-token-here"
```

**3. Launch!**

Build the images and start all services in detached mode.

```bash
docker-compose up -d --build
```

---

## ⚙️ Under the Hood

This project uses a distributed architecture to keep things fast and scalable.

-   **GPU Worker (`gpu/`)**: The core inference engine. It's a custom `llama.cpp` server that connects to Redis.
-   **API Server (`api/`)**: A FastAPI service that handles incoming requests, authenticates them, and pushes jobs to the Redis queue.
-   **Redis**: The message broker that decouples the API from the GPU workers.
-   **Nginx**: A reverse proxy for securely exposing your API to the world.
-   **Monitoring (`monitoring/`)**: A pre-configured Grafana stack with dashboards for Redis and node performance.

---

## 🔌 API Endpoints

Authentication is done via a Bearer token in the `Authorization` header.

| Method | Endpoint       | Description                                |
| :----- | :------------- | :----------------------------------------- |
| `GET`  | `/docs`        | Interactive API documentation.             |
| `POST` | `/generate`    | Queue a text generation job.               |
| `POST` | `/completion`  | Unity-compatible completion endpoint.      |
| `POST` | `/template`    | Get the current chat template.             |
| `POST` | `/tokenize`    | Tokenize a string without generating.      |
| `GET`  | `/health`      | Health check (no auth required).           |

---

## 🎮 Unity Integration

This server is designed to work with Unity assets out-of-the-box.

-   [**LLM for Unity**](https://assetstore.unity.com/packages/tools/ai-ml-integration/llm-for-unity-273604): The recommended asset for connecting your Unity projects to this server.
-   [**Stable Diffusion Unity Integration**](https://github.com/dobrado76/Stable-Diffusion-Unity-Integration/discussions): For discussions on integrating other AI models.
