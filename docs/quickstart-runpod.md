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

### 1. Open the [Runpod template link](https://console.runpod.io/deploy?template=3rsr5dzv50&ref=muhg2w55)

Choose a GPU you want to use. The minimal reccomended GPU for the DND Generator template is the A5000. You can also use a persistent volume to prevent downloading models every time.

### 2. Environment Configuration

In the runpod template you can overwrite any environment variables. The default setup uses the reccomended DND Generator models and hosts the ai inference components standalone (REMOTE=false). If you are already hosting an AI server outside of Runpod, in distributed mode, you need to set Remote=true and the REDIS_URL and REDIS_PASS.

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
SD_STARTUP_COMMAND=./venv/bin/python launch.py --listen --port 7860 --api --skip-torch-cuda-test --no-half-vae --medvram --xformers --skip-version-check
```

### 3. Wait for installation the first run.

The models and pip requirements will be installed the first time and saved on the disk for persistent runs (8gb minimum without any models).

The AI inference server is up and running when you see this in the logs;
```bash

velesio-gpu  | INFO [            start_server] HTTP server listening | tid="135629304680448" timestamp=1760540334 n_threads_http="11" port="1337" hostname="0.0.0.0"

```

### 4. Run!

If you are running in standalone mode, export the ports of LLAMACPP and SD and connect to them directly. If you are running in remote mode, connect to your API server and the runpod GPU worker will pick up jobs from it.

### 5. Connect in Unity!

Refer to one of the Unity integrations sections to start using your AI Inference server in Unity.

## Test

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