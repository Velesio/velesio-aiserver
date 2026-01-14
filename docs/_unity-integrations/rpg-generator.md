---
layout: page
title: PersonaForge
parent: Unity Integrations
nav_order: 3
---


## Introduction
[The PersonaForge Unity asset](https://assetstore.unity.com/preview/335152/1228038) fully utilizes every feature of the Velesio AIServer and is the optimal way to utilize it. Currently the Generator has a minigame scene which features a RPG Character generator that allows playes to generate and talk to RPG characters in various scenarios.

All of the scenes from the asset pack were developed for and tested in Full HD (1920x1080 resolution), that is reccomended for testing.

The AI models stack is used to generate all of the content showcased in the asset's marketing material. Also reccomended for the RPG Generator demo scene since the drop-down menu options are designated to utilize trigger words in the LoRA that is used. The asset's font also requires TMP and TMP Extras to be installed, you can do so from Window > TextMeshPro in the Editor.

```bash
MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q8_0.gguf
SD_MODEL_URL=https://civitai.com/api/download/models/128713?type=Model&format=SafeTensor&size=pruned&fp=fp16
LORA_URL=https://civitai.com/api/download/models/1569286?type=Model&format=SafeTensor
VAE_URL=https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors
```

This model stack is focused around the [RPG Character Maker Lora](https://civitai.com/models/1360012/dnd-character-maker-classes-and-races-concept) and the goal is to create portraits of characters in various contexts with which the player can chat with. All of the dropdown menu options are created to narrow down the options to specific lora keywords.

For more detailed documentation on the LLM for Unity and SD Integration, on which this asset is built on, you can consult their respective documentations.

## Character Generator Scene

This is the primary scene of the Asset. The player fill out various characteristics of a character, or leaves them to be random, a prompt is then made to llamacpp and stablediffusion to generate a background and portrait of the character. The player can then chat with the character with a set context.

The primary configuration game object is the VelesioAI Integration game object, it contains the configurations for the llamacpp and stable diffusion connections as well as the scene itself.

![RPG Generator Scene Overview]({{ '/assets/images/scene.png' | relative_url }})
*Main character generation interface*

You can also utilize a local LLM through the disabled LLM object and unflicking API in the main configuration object.

Within the object, there is a LLMCharacter script, here you can configure the connection to your llamacpp server, most importantly the host and api key.

![LLM Configuration]({{ '/assets/images/object.png' | relative_url }})


Bellow that you will see the SD configuration, here you set the hostname of the SD server (in the example we are pointing to the velesio api server so the url is the same as llamacpp but you might opt to host them completely seperately). Once your SD instance is set up, you have to press 'List models' to load the available models from the server, to be used by calls.

![SD Configuration]({{ '/assets/images/sdconfig.png' | relative_url }})

Within the scene, there is a character portrait, this is where you can find the SD to image script, which generates character portraits. Various configuration settings can be seen in this game object, most importantly the model that should be used. You can generate images in the editor itself but in the active scene this is filled out at runtime.

![Portrait config]({{ '/assets/images/portrait.png' | relative_url }})

All of these components of the scene come together when you fill out the initial form, you essentially create a RPG character, their portrait is generated and then you can chat with them, all through AI.

All of the dropdown options in the scene are there to work optimally with the above reccomended model stack, they are trigger words that the portrait generation model expects to generate a specific character. You can visit the model's Civitai page for further details.

## Simple Connector Demos

In the Asset pack you will also find 3 simple demo scenes for llamacpp, ollama and automatic1111 SD, each of them follows the same idea, just click on the VelesioAI Integration game object, configure the server you're connecting to and follow the instructions in the scene.

## Simple AI Chat

The Asset also features a simple chat feature, simply go to Window > Velesio > AI Chat Window

It can be used for convenient debugging on LLM connectivity as well as brainstorming ideas within Unity and your managed hardware!

---

## Scripts Documentation

```
PersonaForge/
├── Demos/
│   ├── RPG Character Generator/    ← Main demo scene & scripts
│   ├── Simple LlamaCPP/            ← Basic LlamaCPP example
│   ├── Simple Ollama/              ← Basic Ollama example
│   └── Simple SD/                  ← Basic Stable Diffusion example
├── Scripts/
│   ├── Runtime/
│   │   ├── Llamacpp/               ← LlamaCPP integration
│   │   ├── Ollama/                 ← Ollama API wrapper
│   │   └── StableDiffusion/        ← Image generation
│   └── Editor/                     ← Custom inspectors
└── Settings/                       ← ScriptableObject configs
```

---

## Architecture Overview

```
┌─────────────────────────┐
│  CharacterConfigurator  │  ← Collects UI inputs
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│        Prompt.cs        │  ← Builds prompts, calls LLM, triggers SD
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
┌──────────┐  ┌──────────┐
│ LlamaCPP │  │  Ollama  │  ← Dual inference backends
└──────────┘  └──────────┘
            │
            ▼
┌─────────────────────────┐
│   Stable Diffusion      │  ← Portrait generation
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│    RPGCharacter.cs      │  ← Interactive roleplay chat
└─────────────────────────┘
```

---

## RPG Character Generator Scripts

### CharacterConfigurator.cs

**Purpose:** The bridge between the character creation UI and the generation logic. Collects user parameters from the interface and passes them to the `Prompt` script.

**Key Components:**
- **UI Elements:** `TMP_InputField`, `TMP_Dropdown`, and `Toggle` elements for character name, race, class, universe, alignment, level, context, and portrait description.
- **Inference Dropdown:** Selects between "Undream AI" (LlamaCPP) or "Ollama" backends.
- **Dependencies:** Requires references to `Prompt` and `SceneManager` scripts.

**Core Methods:**
| Method | Description |
|--------|-------------|
| `TriggerGeneration()` | Gathers UI inputs, handles randomization, and initiates character generation. |
| `ShowConfiguration()` | Resets UI fields and returns to the configuration view. |
| `ShowLoadingIndicator()` / `HideLoadingIndicator()` | Toggles the loading animation via `SceneManager`. |

---

### Prompt.cs

**Purpose:** The central orchestrator for character generation. Constructs LLM prompts, handles dual inference backends (LlamaCPP/Ollama), parses responses, and triggers portrait generation via Stable Diffusion.

**Key Components:**
- **LLM Components:** `llmCharacter` (LlamaCPP) and `sdImageGenerator` (Stable Diffusion).
- **Ollama Config:** `ollamaUrl` and `ollamaModel` for local Ollama inference.
- **Prompt Templates:** `characterPrompt`, `portraitStylePrefix`, and `negativePrompt`.

**Core Methods:**
| Method | Description |
|--------|-------------|
| `StartCharacterGeneration(...)` | Main entry point. Builds prompts, calls LLM, parses results, triggers image generation. |
| `GenerateWithOllama(string prompt)` | Handles streaming generation via the Ollama backend. |
| `BuildComprehensiveImagePrompt(...)` | Creates a detailed Stable Diffusion prompt from the character description. |
| `DisplayCharacterPortrait(Texture2D)` | Callback that applies the generated portrait texture to the UI. |
| `CancelRequest()` | Stops ongoing requests and resets UI state. |

---

### RPGCharacter.cs

**Purpose:** Manages the interactive roleplay chat after character generation. Maintains conversation context and supports both LlamaCPP and Ollama backends.

**Key Components:**
- **`llmCharacter`:** LlamaCPP component for chat responses.
- **Ollama Config:** `ollamaUrl` and `ollamaModel` for local inference.
- **`chatHistory`:** Stores the conversation log.

**Core Methods:**
| Method | Description |
|--------|-------------|
| `SetCharacterContext(...)` | Initializes the chat with the character's details and triggers an opening remark. |
| `onInputFieldSubmit(string message)` | Sends player messages to the LLM and displays the streamed response. |
| `SetAIText(string text)` | Updates the chat display during response streaming. |

---

### SceneManager.cs

**Purpose:** A simple UI state machine that manages panel visibility for different application states.

**Key Components:**
- **UI Panels:** `configurationPanel`, `backgroundPanel`, `chatPanel`, `loadingIndicator`.
- **`SceneState` Enum:** `Configuration`, `Background`, `Chat`.

**Core Methods:**
| Method | Description |
|--------|-------------|
| `SwitchToScene(SceneState newState)` | Activates the appropriate panels for the given state. |
| `ShowLoadingIndicator(bool show)` | Toggles the loading indicator visibility. |
| `UpdateCurrentSituation(string text)` | Updates the "Current Situation" text on the background panel. |
| `ResetToConfiguration()` | Returns the UI to the initial configuration state. |

---

## LlamaCPP Integration

Located in `Scripts/Runtime/Llamacpp/`

### How It Works

LlamaCPP provides high-performance LLM inference. The integration connects to a **remote llama.cpp server** (local server management has been removed for simplicity).

### Key Scripts

| Script | Purpose |
|--------|---------|
| `LLM.cs` | Server configuration component. Manages connection settings (port, context size, API key). |
| `LLMCaller.cs` | Base class for making LLM requests. Handles local/remote switching and request management. |
| `LLMChatTemplates.cs` | Chat template definitions for different model formats. |
| `LLMInterface.cs` | Request/response data structures for the llama.cpp API. |

### Basic Usage

```csharp
// LLMCaller handles the connection
public LLMCaller llmCharacter;

// Send a chat message and receive streaming response
string response = await llmCharacter.Chat(prompt, OnPartialResponse);

// Callback for streaming tokens
void OnPartialResponse(string partial) {
    responseText.text = partial;
}
```

### Configuration

- **Remote Mode:** Set `remote = true` and configure `host` (e.g., `localhost:13333`).
- **Context Size:** Adjust `contextSize` on the `LLM` component (default: 8192).
- **Chat Template:** Set the appropriate template for your model in `chatTemplate`.

---

## Ollama Integration

Located in `Scripts/Runtime/Ollama/`

### How It Works

Ollama provides a simple REST API for running LLMs locally. The integration wraps the Ollama API with async/await patterns and streaming support.

### Key Scripts

| Script | Purpose |
|--------|---------|
| `Chat.cs` | Chat completions with history management. Supports streaming responses. |
| `Generate.cs` | Raw text generation without chat context. |
| `Embeddings.cs` | Generate vector embeddings for RAG applications. |
| `RAG.cs` | Retrieval Augmented Generation helpers. |
| `ToolCalling.cs` | Function/tool calling support. |
| `Payload.cs` | Request/response data structures. |

### Basic Usage

```csharp
// Initialize a chat session
Ollama.InitChat(historyLimit: 8, system: "You are a helpful assistant.");

// Send a chat message (non-streaming)
string response = await Ollama.Chat("gemma3:4b", "Hello!");

// Send a chat message (streaming)
await Ollama.ChatStream(
    onTextReceived: (text) => responseText.text += text,
    model: "gemma3:4b",
    prompt: "Tell me a story"
);
```

### Configuration

- **Server URL:** Configure via `OllamaSettings` ScriptableObject or directly in scripts.
- **Model:** Use Ollama model syntax (e.g., `gemma3:4b`, `llama3:8b`).
- **Keep Alive:** Set how long the model stays loaded in memory (default: 300 seconds).

### Chat History

```csharp
// Save chat to disk
Ollama.SaveChatHistory("mychat.dat");

// Load chat from disk
Ollama.LoadChatHistory("mychat.dat", historyLimit: 8);
```

---

## Stable Diffusion Integration

Located in `Scripts/Runtime/StableDiffusion/`

### How It Works

Connects to an **Automatic1111 Stable Diffusion WebUI** server to generate images from text prompts.

### Key Scripts

| Script | Purpose |
|--------|---------|
| `StableDiffusionGenerator.cs` | Base class with progress tracking and server communication. |
| `StableDiffusionText2Image.cs` | Generate images from text prompts. |
| `StableDiffusionImage2Image.cs` | Transform existing images with prompts. |
| `StableDiffusionText2Material.cs` | Generate PBR materials from text. |
| `StableDiffusionConfiguration.cs` | Server profiles and global settings. |
| `SDSettings.cs` | Per-profile generation defaults. |

### Basic Usage

```csharp
public StableDiffusionText2Image sdGenerator;

// Configure the prompt
sdGenerator.prompt = "fantasy warrior portrait, detailed, dramatic lighting";
sdGenerator.negativePrompt = "blurry, low quality";
sdGenerator.width = 512;
sdGenerator.height = 512;
sdGenerator.steps = 30;

// Subscribe to completion event
sdGenerator.OnImageGenerated.AddListener(OnPortraitGenerated);

// Generate
sdGenerator.Generate();

void OnPortraitGenerated(Texture2D texture) {
    portraitImage.texture = texture;
}
```

### Configuration

- **Server URL:** Configure in `StableDiffusionConfiguration` component.
- **Sampler:** Select from available samplers (e.g., `Euler a`, `DPM++ 2M`).
- **Model:** Select from models available on your SD server.
- **Parameters:**
  - `steps`: Number of diffusion steps (higher = better quality, slower).
  - `cfgScale`: How closely to follow the prompt (7-12 typical).
  - `seed`: Use `-1` for random, or set a specific seed for reproducibility.
  - `width/height`: Image dimensions (128-2048, must be multiples of 8).

### Server Profiles

Use `StableDiffusionConfiguration` to manage multiple server profiles:
- Local development server
- Remote production server
- Different model configurations

---

## Quick Reference: Dual Inference Support

The asset supports two LLM backends:

| Backend | Use Case | Configuration |
|---------|----------|---------------|
| **LlamaCPP** | Remote llama.cpp server | Set `host` and `port` on `LLM` component |
| **Ollama** | Local Ollama server | Set URL and model in scripts or `OllamaSettings` |

Select your preferred backend via the **Inference Method** dropdown in the character configuration UI.

---

## Need Help?

- [Full Documentation](https://velesio.github.io/velesio-aiserver/unity-integrations/rpg-generator/)
- [Discord Support](https://discord.gg/9c6JZedYNc)
