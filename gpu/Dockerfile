FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv curl wget git \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements for reference but don't install yet
COPY requirements.txt /app/

# Copy application code
COPY entrypoint.sh /app/
COPY *.py /app/

# Copy llama binaries
COPY libundreamai_linux-cuda-cu12.2.0.so /app/
COPY undreamai_server /app/

RUN chmod +x entrypoint.sh

# Create directory structure for mounted volumes
RUN mkdir -p /app/data/models/text /app/data/models/image /app/data/sd

CMD ["./entrypoint.sh"]
