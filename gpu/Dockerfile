FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv curl wget git \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files first (for better caching)
COPY requirements.txt /app/
COPY entrypoint.sh /app/
COPY *.py /app/

# Copy only the llama binary (exclude models and SD)
COPY data/llama/libundreamai_linux-cuda-cu12.2.0.so /app/data/llama/
COPY data/llama/undreamai_server /app/data/llama/

RUN chmod +x entrypoint.sh

# Install your requirements with CUDA support
RUN pip install --no-cache-dir torch torchvision torchaudio xformers --index-url https://download.pytorch.org/whl/cu124
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure for mounted volumes
RUN mkdir -p /app/data/models/text /app/data/models/image /app/data/sd

CMD ["./entrypoint.sh"]
