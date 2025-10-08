---
layout: page
title: Runpod Quickstart
nav_order: 2
---

## Prerequisites

In runpod only the GPU component can be hosted, you can either host it standalone with REMOTE set to false, or connect it to an external API service. Hosting the API service in runpod is not possible for now since they don't support firewall configurations.

Before you begin, ensure you have:

- **A Runpod account** if you don't have one yet, you can use my [refferal link](https://runpod.io?ref=muhg2w55) to get a 5$ starting bonus!
- If you are running in REMOTE mode, you need to host the API server externally from Rupod, on AWS Lightsail for example. Make sure to open the redis port just to the Runpod worker's IP for optimal security. For a testing setup, its best to just start off with REMOTE=false.


## Steps

### 1. Open the [Runpod template link](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55) and choose a GPU you want to use. The minimal reccomended GPU for the DND Generator template is the A5000.

### 2. Environment Configuration

In the runpod template you must configure your environment variables.

```bash
# LLAMACPP Server Startup Command
STARTUP_COMMAND=./undreamai_server --model /app/data/models/text/model.gguf --host 0.0.0.0 --port 1337 --gpu-layers 37 --template chatml

#Connectivity
REMOTE=false # false does not connect llamacpp server to api
REDIS_HOST=redis
REDIS_PASS=secure_redis_pass

#UndreamAI Server Settings
MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q8_0.gguf

#Stable Diffusion Settings
RUN_SD=true
SD_MODEL_URL=https://civitai.com/api/download/models/128713?type=Model&format=SafeTensor&size=pruned&fp=fp16
LORA_URL=https://civitai.com/api/download/models/110115?type=Model&format=SafeTensor
VAE_URL=https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors
```

### 4. Run!

If you are running in standalone mode, export the ports of LLAMACPP and SD and connect to them directly. If you are running in remote mode, connect to your API server and the runpod GPU worker will pick up jobs from it.

### 5. Connect in Unity!

Refer to one of the Unity integrations sections to start using your AI Inference server in Unity.

## First API Call

Test your installation with a simple API call:

```bash
curl -X POST http://localhost:8000/completion \
  -H "Authorization: Bearer secure_token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms:",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

Expected response:
```json
{
  "choices": [
    {
      "text": "Quantum computing is a revolutionary approach to computation...",
      "finish_reason": "length"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 100,
    "total_tokens": 108
  }
}
```