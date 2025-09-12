FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies in one layer and clean up
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv curl wget git \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 🎯 COPY REQUIREMENTS FIRST (for better caching)
COPY requirements.txt /app/

# 🎯 INSTALL PYTHON PACKAGES BEFORE COPYING CODE
RUN pip install --no-cache-dir torch torchvision torchaudio xformers --index-url https://download.pytorch.org/whl/cu124 \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip \
    && find /usr/local/lib/python3.10/dist-packages -name "*.pyc" -delete \
    && find /usr/local/lib/python3.10/dist-packages -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 🎯 COPY APPLICATION CODE LAST
COPY entrypoint.sh /app/
COPY *.py /app/

# Copy only the llama binary (exclude models and SD)
COPY data/llama/libundreamai_linux-cuda-cu12.2.0.so /app/data/llama/
COPY data/llama/undreamai_server /app/data/llama/

RUN chmod +x entrypoint.sh

# Create directory structure for mounted volumes
RUN mkdir -p /app/data/models/text /app/data/models/image /app/data/sd

CMD ["./entrypoint.sh"]
