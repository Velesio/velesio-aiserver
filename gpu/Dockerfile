FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 python3-venv python3-distutils python3-pip wget ca-certificates git \
    build-essential cmake ninja-build libcurl4-openssl-dev binutils \
    libcurl4 libgomp1 libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt llm.py ollama_llm.py sd.py entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh

CMD ["./entrypoint.sh"]
