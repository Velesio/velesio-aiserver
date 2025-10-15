---
layout: page
title: GPU Workers
parent: Components
nav_order: 2
---

# GPU Workers

The GPU workers are specialized containers that handle AI inference tasks using NVIDIA GPUs.

## Overview

**Location**: `gpu/`  
**Technology**: Python + CUDA + Custom Binaries  
**Container**: `Velesio-gpu`  
**Workers**: LLM Worker (`llm.py`) + Stable Diffusion Worker (`sd.py`)

The GPU workers pull jobs from Redis queue and execute AI inference using:

- **LLM Worker**: Custom `undreamai_server` (llama.cpp fork) for text generation
- **SD Worker**: Automatic1111 WebUI for image generation

## Architecture

```
┌─────────────────────────────────────────┐
│              GPU Worker                 │
│                                         │
│  ┌─────────────┐    ┌─────────────────┐ │
│  │ Job Poller  │    │  Result Writer  │ │
│  │  (Redis)    │    │    (Redis)      │ │
│  └─────┬───────┘    └─────────▲───────┘ │
│        │                      │         │
│        ▼                      │         │
│  ┌─────────────────────────────┴───────┐ │
│  │         Job Processor              │ │
│  │                                    │ │
│  │  ┌─────────────┐ ┌───────────────┐ │ │
│  │  │ LLM Engine  │ │  SD Engine    │ │ │
│  │  │             │ │               │ │ │
│  │  │undreamai_   │ │ Automatic1111 │ │ │
│  │  │server       │ │   WebUI       │ │ │
│  │  └─────────────┘ └───────────────┘ │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │              GPU Memory             │ │
│  │  ┌─────────────┐ ┌───────────────┐  │ │
│  │  │ LLM Models  │ │  SD Models    │  │ │
│  │  │ (.gguf)     │ │ (.safetensors)│  │ │
│  │  └─────────────┘ └───────────────┘  │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## LLM Worker (`llm.py`)

### Core Technology

**Engine**: `undreamai_server` - Custom llama.cpp fork optimized for undream.ai

**Key Features**:
- GGUF model format support
- GPU layer offloading (CUDA)
- Streaming text generation
- Context window management
- Memory-efficient inference

### Implementation

```python
import subprocess
import json
import time
import redis
from typing import Dict, Any

class LLMWorker:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379)
        self.server_process = None
        self.model_loaded = False
        
    def start_server(self):
        """Start the undreamai_server process"""
        cmd = [
            './data/llama/undreamai_server',
            '--model', './data/models/text/model.gguf',
            '--ctx-size', '4096',
            '--n-gpu-layers', str(os.getenv('GPU_LAYERS', 35)),
            '--host', '0.0.0.0',
            '--port', '1337'
        ]
        
        self.server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        self.wait_for_server()
        self.model_loaded = True
        
    def wait_for_server(self):
        """Wait for server to be ready"""
        import requests
        for _ in range(60):  # 60 second timeout
            try:
                response = requests.get('http://localhost:1337/health')
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)
        raise Exception("Server failed to start")
```

### Job Processing

```python
def process_completion_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process text completion job"""
    
    # Extract parameters
    prompt = job_data.get('prompt', '')
    max_tokens = job_data.get('max_tokens', 150)
    temperature = job_data.get('temperature', 0.7)
    
    # Prepare request to undreamai_server
    payload = {
        'prompt': prompt,
        'n_predict': max_tokens,
        'temperature': temperature,
        'top_k': job_data.get('top_k', 40),
        'top_p': job_data.get('top_p', 0.9),
        'repeat_penalty': 1.1,
        'stream': job_data.get('stream', False)
    }
    
    try:
        # Send request to local server
        response = requests.post(
            'http://localhost:1337/completion',
            json=payload,
            timeout=300
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Format response
        return {
            'text': result['content'],
            'finish_reason': result.get('stop_reason', 'stop'),
            'usage': {
                'prompt_tokens': result.get('tokens_evaluated', 0),
                'completion_tokens': result.get('tokens_predicted', 0),
                'total_tokens': result.get('tokens_evaluated', 0) + result.get('tokens_predicted', 0)
            }
        }
        
    except Exception as e:
        return {'error': str(e)}
```

### Streaming Support

```python
def process_streaming_job(self, job_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """Process streaming completion job"""
    
    payload = {
        'prompt': job_data.get('prompt', ''),
        'n_predict': job_data.get('max_tokens', 150),
        'temperature': job_data.get('temperature', 0.7),
        'stream': True
    }
    
    try:
        response = requests.post(
            'http://localhost:1337/completion',
            json=payload,
            stream=True,
            timeout=300
        )
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'content' in data:
                        yield {
                            'choices': [{
                                'text': data['content'],
                                'index': 0,
                                'finish_reason': None
                            }]
                        }
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        yield {'error': str(e)}
```

### Model Management

```python
def load_model(self, model_path: str):
    """Load a specific model"""
    
    # Stop current server if running
    if self.server_process:
        self.server_process.terminate()
        self.server_process.wait()
    
    # Start with new model
    self.start_server_with_model(model_path)
    
def get_model_info(self) -> Dict[str, Any]:
    """Get information about loaded model"""
    try:
        response = requests.get('http://localhost:1337/props')
        response.raise_for_status()
        
        props = response.json()
        return {
            'name': props.get('default_generation_settings', {}).get('model', 'unknown'),
            'context_length': props.get('default_generation_settings', {}).get('n_ctx', 0),
            'vocab_size': props.get('vocab_size', 0),
            'total_params': props.get('n_params', 0)
        }
    except:
        return {'error': 'Failed to get model info'}
```

## Stable Diffusion Worker (`sd.py`)

### Core Technology

**Engine**: Automatic1111 WebUI  
**Framework**: PyTorch + Diffusers  
**Acceleration**: xFormers, Flash Attention

### Implementation

```python
import requests
import base64
import io
from PIL import Image

class SDWorker:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379)
        self.webui_url = 'http://localhost:7860'
        self.initialized = False
        
    def start_webui(self):
        """Start Automatic1111 WebUI"""
        cmd = [
            'python', 'webui.py',
            '--api',
            '--listen',
            '--port', '7860',
            '--xformers',
            '--no-gradio-queue'
        ]
        
        self.webui_process = subprocess.Popen(
            cmd,
            cwd='./data/sd',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.wait_for_webui()
        self.initialized = True
        
    def wait_for_webui(self):
        """Wait for WebUI to be ready"""
        for _ in range(120):  # 2 minute timeout
            try:
                response = requests.get(f'{self.webui_url}/sdapi/v1/progress')
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)
        raise Exception("WebUI failed to start")
```

### Text-to-Image Processing

```python
def process_txt2img_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process text-to-image generation job"""
    
    payload = {
        'prompt': job_data.get('prompt', ''),
        'negative_prompt': job_data.get('negative_prompt', ''),
        'width': job_data.get('width', 512),
        'height': job_data.get('height', 512),
        'steps': job_data.get('steps', 20),
        'cfg_scale': job_data.get('cfg_scale', 7.5),
        'sampler_name': job_data.get('sampler_name', 'Euler a'),
        'seed': job_data.get('seed', -1),
        'batch_size': job_data.get('batch_size', 1),
        'n_iter': job_data.get('n_iter', 1)
    }
    
    try:
        response = requests.post(
            f'{self.webui_url}/sdapi/v1/txt2img',
            json=payload,
            timeout=600  # 10 minute timeout for image generation
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'images': result['images'],  # Base64 encoded images
            'parameters': {
                'prompt': payload['prompt'],
                'steps': payload['steps'],
                'seed': result.get('info', {}).get('seed', payload['seed']),
                'width': payload['width'],
                'height': payload['height']
            },
            'info': result.get('info', '')
        }
        
    except Exception as e:
        return {'error': str(e)}
```

### Image-to-Image Processing

```python
def process_img2img_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process image-to-image transformation job"""
    
    # Decode input images
    init_images = []
    for img_b64 in job_data.get('init_images', []):
        img_data = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_data))
        init_images.append(img)
    
    payload = {
        'init_images': job_data.get('init_images', []),
        'prompt': job_data.get('prompt', ''),
        'negative_prompt': job_data.get('negative_prompt', ''),
        'denoising_strength': job_data.get('denoising_strength', 0.75),
        'width': job_data.get('width', 512),
        'height': job_data.get('height', 512),
        'steps': job_data.get('steps', 20),
        'cfg_scale': job_data.get('cfg_scale', 7.5)
    }
    
    try:
        response = requests.post(
            f'{self.webui_url}/sdapi/v1/img2img',
            json=payload,
            timeout=600
        )
        response.raise_for_status()
        
        result = response.json()
        return format_sd_response(result, payload)
        
    except Exception as e:
        return {'error': str(e)}
```

### Model Management

```python
def list_models(self) -> Dict[str, Any]:
    """List available Stable Diffusion models"""
    try:
        response = requests.get(f'{self.webui_url}/sdapi/v1/sd-models')
        response.raise_for_status()
        
        models = response.json()
        return {
            'models': [
                {
                    'name': model['title'],
                    'filename': model['filename'],
                    'hash': model.get('hash', ''),
                    'loaded': model.get('model_name') == self.get_current_model()
                }
                for model in models
            ]
        }
    except Exception as e:
        return {'error': str(e)}

def switch_model(self, model_name: str) -> Dict[str, Any]:
    """Switch to a different SD model"""
    try:
        payload = {'sd_model_checkpoint': model_name}
        response = requests.post(
            f'{self.webui_url}/sdapi/v1/options',
            json=payload
        )
        response.raise_for_status()
        
        return {'success': True, 'model': model_name}
    except Exception as e:
        return {'error': str(e)}
```

## Job Queue Integration

### Redis Job Polling

```python
def main_worker_loop(self):
    """Main worker loop - polls Redis for jobs"""
    
    llm_worker = LLMWorker()
    sd_worker = SDWorker()
    
    # Initialize workers
    llm_worker.start_server()
    if os.getenv('RUN_SD', 'true').lower() == 'true':
        sd_worker.start_webui()
    
    while True:
        try:
            # Poll Redis queue (blocking pop with timeout)
            job_data = self.redis_client.brpop('llama_queue', timeout=10)
            
            if job_data:
                queue_name, job_json = job_data
                job = json.loads(job_json)
                
                # Process job based on type
                result = self.process_job(job, llm_worker, sd_worker)
                
                # Store result in Redis
                result_key = f"result:{job['id']}"
                self.redis_client.setex(
                    result_key,
                    3600,  # 1 hour TTL
                    json.dumps(result)
                )
                
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(1)
```

### Job Processing Router

```python
def process_job(self, job: Dict[str, Any], llm_worker: LLMWorker, sd_worker: SDWorker) -> Dict[str, Any]:
    """Route job to appropriate worker"""
    
    job_type = job.get('type', '')
    job_data = job.get('data', {})
    
    try:
        if job_type == 'completion':
            return llm_worker.process_completion_job(job_data)
        elif job_type == 'chat_completion':
            return llm_worker.process_chat_completion_job(job_data)
        elif job_type == 'txt2img':
            return sd_worker.process_txt2img_job(job_data)
        elif job_type == 'img2img':
            return sd_worker.process_img2img_job(job_data)
        else:
            return {'error': f'Unknown job type: {job_type}'}
            
    except Exception as e:
        return {'error': str(e)}
```

## GPU Memory Management

### Dynamic Memory Allocation

```python
def optimize_gpu_memory(self):
    """Optimize GPU memory usage"""
    
    # Get available GPU memory
    import pynvml
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    
    available_mb = mem_info.free // 1024 // 1024
    
    # Adjust model parameters based on available memory
    if available_mb < 4000:  # Less than 4GB
        self.gpu_layers = min(self.gpu_layers, 20)
        self.context_size = min(self.context_size, 2048)
    elif available_mb < 8000:  # Less than 8GB
        self.gpu_layers = min(self.gpu_layers, 30)
        self.context_size = min(self.context_size, 4096)
```

### Model Unloading

```python
def unload_model_if_needed(self):
    """Unload model to free GPU memory"""
    
    # Check if no jobs processed recently
    last_job_time = self.redis_client.get('last_job_time')
    if last_job_time:
        elapsed = time.time() - float(last_job_time)
        if elapsed > 300:  # 5 minutes idle
            self.unload_models()

def unload_models(self):
    """Unload all models from GPU memory"""
    if self.llm_worker.server_process:
        self.llm_worker.server_process.terminate()
        self.llm_worker.model_loaded = False
    
    # Clear GPU cache
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
```

## Performance Optimization

### Batch Processing

```python
def process_batch_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process multiple jobs in batch for efficiency"""
    
    # Group jobs by type
    txt2img_jobs = [j for j in jobs if j['type'] == 'txt2img']
    completion_jobs = [j for j in jobs if j['type'] == 'completion']
    
    results = []
    
    # Process image generation jobs in batch
    if txt2img_jobs:
        batch_result = self.sd_worker.process_batch_txt2img(txt2img_jobs)
        results.extend(batch_result)
    
    # Process text completion jobs sequentially (for now)
    for job in completion_jobs:
        result = self.llm_worker.process_completion_job(job['data'])
        results.append(result)
    
    return results
```

### Caching

```python
def cache_frequently_used_prompts(self, prompt: str, result: Dict[str, Any]):
    """Cache results for frequently used prompts"""
    
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    cache_key = f"prompt_cache:{prompt_hash}"
    
    # Store in Redis with TTL
    self.redis_client.setex(
        cache_key,
        7200,  # 2 hours
        json.dumps(result)
    )

def get_cached_result(self, prompt: str) -> Optional[Dict[str, Any]]:
    """Get cached result for prompt"""
    
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    cache_key = f"prompt_cache:{prompt_hash}"
    
    cached = self.redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    return None
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GPU_LAYERS` | `35` | Number of model layers on GPU |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device ID |
| `MODEL_PATH` | `./data/models/text/model.gguf` | LLM model path |
| `SD_MODEL_PATH` | `./data/models/image/` | SD models directory |
| `CONTEXT_SIZE` | `4096` | LLM context window |
| `RUN_SD` | `true` | Enable Stable Diffusion |
| `STARTUP_COMMAND` | `./undreamai_server --model...` | LLM server startup command |
| `SD_STARTUP_COMMAND` | `./venv/bin/python launch.py...` | Stable Diffusion startup command |
| `REDIS_URL` | `redis://redis:6379` | Redis connection |
| `WORKER_TIMEOUT` | `600` | Job processing timeout |

### Docker Configuration

```dockerfile
FROM nvidia/cuda:11.8-devel-ubuntu20.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip git wget curl

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy worker code
COPY llm.py sd.py ./
COPY data/ ./data/

# Set permissions
RUN chmod +x ./data/llama/undreamai_server

# Non-root user
RUN useradd -m -u 1000 worker
USER worker

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:1337/health')"

# Start worker
CMD ["python3", "llm.py"]
```

## Monitoring

### Worker Health Checks

```python
def health_check(self) -> Dict[str, Any]:
    """Comprehensive worker health check"""
    
    health = {
        'timestamp': time.time(),
        'gpu_available': torch.cuda.is_available(),
        'models_loaded': {}
    }
    
    # Check LLM worker
    try:
        response = requests.get('http://localhost:1337/health', timeout=5)
        health['llm_worker'] = response.status_code == 200
        health['models_loaded']['llm'] = self.llm_worker.model_loaded
    except:
        health['llm_worker'] = False
        health['models_loaded']['llm'] = False
    
    # Check SD worker
    if os.getenv('RUN_SD', 'true').lower() == 'true':
        try:
            response = requests.get('http://localhost:7860/sdapi/v1/progress', timeout=5)
            health['sd_worker'] = response.status_code == 200
            health['models_loaded']['sd'] = self.sd_worker.initialized
        except:
            health['sd_worker'] = False
            health['models_loaded']['sd'] = False
    
    # GPU memory info
    if torch.cuda.is_available():
        health['gpu_memory'] = {
            'allocated': torch.cuda.memory_allocated(),
            'cached': torch.cuda.memory_reserved(),
            'total': torch.cuda.get_device_properties(0).total_memory
        }
    
    return health
```

### Performance Metrics

```python
def log_performance_metrics(self, job_type: str, duration: float, success: bool):
    """Log performance metrics"""
    
    metrics = {
        'job_type': job_type,
        'duration': duration,
        'success': success,
        'timestamp': time.time(),
        'gpu_utilization': self.get_gpu_utilization()
    }
    
    # Store in Redis for monitoring
    metrics_key = f"metrics:{int(time.time())}"
    self.redis_client.setex(metrics_key, 86400, json.dumps(metrics))  # 24 hour TTL
```

## Troubleshooting

### Common Issues

1. **Model Loading Failures**
   ```python
   # Check model file exists and is readable
   import os
   model_path = './data/models/text/model.gguf'
   if not os.path.exists(model_path):
       print(f"Model file not found: {model_path}")
   elif not os.access(model_path, os.R_OK):
       print(f"Model file not readable: {model_path}")
   ```

2. **GPU Memory Issues**
   ```python
   # Monitor GPU memory usage
   import pynvml
   pynvml.nvmlInit()
   handle = pynvml.nvmlDeviceGetHandleByIndex(0)
   mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
   print(f"GPU Memory: {mem_info.used/1024**3:.1f}GB used, {mem_info.free/1024**3:.1f}GB free")
   ```

3. **Worker Communication Issues**
   ```python
   # Test Redis connectivity
   try:
       self.redis_client.ping()
       print("Redis connection OK")
   except Exception as e:
       print(f"Redis connection failed: {e}")
   ```

### Debug Mode

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add timing information
import time
def timed_function(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.2f} seconds")
        return result
    return wrapper
```

## Next Steps

- [Redis Queue](redis-queue.html) - Understand job queue management
- [API Service](api-service.html) - Learn about API integration
- [Monitoring](monitoring.html) - Set up GPU monitoring