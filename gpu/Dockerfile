FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv curl wget git \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy your app files
COPY . /app
RUN chmod +x entrypoint.sh

# Install your requirements
RUN pip install --no-cache-dir -r requirements.txt

CMD ["./entrypoint.sh"]
