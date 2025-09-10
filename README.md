# 🚀 Graycat AI Server 🚀

Plug and play AI Inference with a focus on compatibility with Unity.
---

## ✨ Features

*   **Ease of Use:** Microservice architecture allows for flexible methods of deployment for any user case.
*   **Unity Ready:** Seamless integration with a selection of Unity Assets.
*   **Scalability:** Built with Docker and a worker-queue architecture to handle any load from anywhere.
*   **Hosting:** Token-based authentication and Nginx Reverse proxy setup.
*   **Observability:** Grafana monitoring stack to keep an eye on everything.

---
## Runpod Quickstart for GPU module hosting [Template Link](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55)
*   **REMOTE: false** Hosts the LLAMACPP endpoint on the exposed port (1337 by default).
*   **REMOTE: true** Connects to remote API Server's redis queue (port 6379 by default). In that case you do not need to expose any ports. It is Reccomended to have a Firewall on your API Server's end and only allow the GPU worker IPs on the Redis port.

## 🔌 Environment Variables

| ENV              | Service(s) | Description                                                                                                 | Default/Example                                                              |
| :--------------- | :--------- | :---------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------- |
| `API_TOKENS`     | `api`      | Comma-separated list of valid bearer tokens for authenticating API requests.                                | `your-secret-token-here`                                                     |
| `MODEL_URL`      | `gpu`      | The URL to download the GGUF model from if not already present in `gpu/models`.                               | `https://huggingface.co/.../qwen2.5-3b-instruct-q8_0.gguf`                   |
| `REDIS_HOST`     | `api`, `gpu` | The hostname of the Redis server.                                                                           | `redis`                                                                      |
| `REDIS_PASS`     | `redis`, `api`, `gpu` | The password for the Redis server.                                                                          | `your_secure_password`                                                       |
| `LLAMA_SERVER_URL` | `gpu`      | The URL of the llama.cpp server endpoint. Used by the worker to know where to send inference requests.      | `http://localhost:1337`                                                      |
| `GPU_LAYERS`     | `gpu`      | The number of model layers to offload to the GPU. Set to `0` for CPU-only.                                  | `30`                                                                         |
| `PORT`           | `gpu`      | The port the internal `undreamai_server` will listen on.                                                    | `1337`                                                                       |
| `REMOTE`         | `gpu`      | If `true`, the GPU worker connects to a remote Redis queue. If `false`, it hosts its own endpoint.            | `true`                                                                       |

---

## 🏁 Self Hosted Setup Instructions

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

Create a `.env` file in the root directory and add your env vars.

**3. Launch!**

Build the images and start all services in detached mode. You can comment out or remove specific services depending on what you want to run.

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
