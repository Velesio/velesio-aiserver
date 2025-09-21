---
layout: page
title: Stable Diffusion for Unity
parent: Unity Integrations
nav_order: 2
---

# Stable Diffusion for Unity

A Unity integration that connects [Stable-Diffusion-Unity-Integration](https://github.com/dobrado76/Stable-Diffusion-Unity-Integration) to Velesio AI Server for real-time image generation.

## Technical Overview

This integration provides a bridge between Unity and Velesio AI Server's Stable Diffusion endpoints:

```
Unity Game → SD Unity Package → HTTP POST → Velesio AI Server → Generated Image
```

### API Integration

**Text-to-Image Endpoint**: `POST /txt2img`

**Request Format**:
```json
{
  "prompt": "a magical forest with glowing mushrooms",
  "negative_prompt": "blurry, low quality",
  "width": 512,
  "height": 512,
  "steps": 20,
  "cfg_scale": 7.5,
  "seed": -1
}
```

**Image-to-Image Endpoint**: `POST /img2img`

**Request Format**:
```json
{
  "prompt": "convert to cyberpunk style",
  "init_images": ["base64_encoded_image"],
  "denoising_strength": 0.7,
  "width": 512,
  "height": 512
}
```

**Response Format**:
```json
{
  "images": ["base64_encoded_generated_image"],
  "parameters": {
    "prompt": "...",
    "seed": 12345,
    "steps": 20
  }
}
```

### Unity Implementation

Configure the SD Unity package to use Velesio AI Server as the backend:

```csharp
// Configure Stable Diffusion to use Velesio AI Server
var sdConfig = new StableDiffusionConfig
{
    serverUrl = "http://your-Velesio-server.com:8000",
    apiEndpoint = "/txt2img",
    timeout = 30f
};

// Generate image
var request = new ImageGenerationRequest
{
    prompt = "fantasy landscape",
    width = 512,
    height = 512
};

var imageData = await sdClient.GenerateImageAsync(request);
var texture = Convert.FromBase64ToTexture2D(imageData.images[0]);
```

### Authentication

Include API token in request headers:
```
Authorization: Bearer your-api-token
Content-Type: application/json
```

### Benefits

- **Remote Processing**: Leverages powerful GPU servers for generation
- **Real-time Generation**: Create images during gameplay
- **Multiple Models**: Server-side model switching capability
- **Memory Efficient**: No local VRAM requirements