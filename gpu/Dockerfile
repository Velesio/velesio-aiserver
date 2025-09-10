FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies for A1111 + your existing stuff
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv curl wget git \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Clone Automatic1111 WebUI
RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git /opt/automatic1111

# Set up A1111 environment
WORKDIR /opt/automatic1111
RUN python3 -m venv venv
RUN ./venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Create models directory structure
RUN mkdir -p models/Stable-diffusion models/VAE models/Lora models/embeddings

# Copy your app files
WORKDIR /app
COPY . /app
RUN chmod +x entrypoint.sh

# Install your requirements
RUN pip install --no-cache-dir -r requirements.txt

CMD ["./entrypoint.sh"]
