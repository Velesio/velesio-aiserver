---
layout: page
title: DND Generator
parent: Unity Integrations
nav_order: 3
---


## Introduction
The RPG Character Generator Unity asset fully utilizes every feature of the Velesio AIServer and is the optimal way to utilize it. Currently the Generator has one scene which features a RPG Character generator that allows playes to generate and talk to DND characters in various scenarios.

To optimally experience the asset it is reccomended to utilize the RPG Character model stack.

```bash
MODEL_URL=https://huggingface.co/DavidAU/Llama-3.-8X3B-MOE-Dark-Champion-Instruct-uncensored-abliterated-18.4B-GGUF/resolve/main/L3.2-8X3B-MOE-Dark-Champion-Inst-18.4B-uncen-ablit_D_AU-Q3_k_s.gguf
SD_MODEL_URL=https://civitai.com/api/download/models/128713?type=Model&format=SafeTensor&size=pruned&fp=fp16
LORA_URL=https://civitai.com/api/download/models/1569286?type=Model&format=SafeTensor
VAE_URL=https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors
```

This model stack is focused around the [DND Character Maker Lora](https://civitai.com/models/1360012/dnd-character-maker-classes-and-races-concept) and the goal is to create portraits of characters in various contexts with which the player can chat with. All of the dropdown menu options are created to narrow down the options to specific lora keywords.



## Character Generator Scene

This is the primary scene of the Asset. The player fill out various characteristics of a character, or leaves them to be random, a prompt is then made to llamacpp and stabledifussion to generate a background and portrait of the character. The player can then chat with the character with a set context.

The primary configuration game object is the VelesioAI Integration game object, it contains the configurations for the llamacpp and stable diffusion connections as well as the scene itself:
- LLAMACPP Configuration's most important component is the address where llamacpp is running, by default variables in Unity are the default variables of the VelesioAI Server when you host it with the example variables.

<img src="{{ '/assets/dnd-image.png' | relative_url }}" alt="DND Generator" style="width: 100%; height: auto;" />

