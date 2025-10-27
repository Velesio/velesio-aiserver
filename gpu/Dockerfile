# # Build
# FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder
# WORKDIR /build

# RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
#     git build-essential cmake ninja-build libcurl4-openssl-dev binutils ca-certificates \
#  && rm -rf /var/lib/apt/lists/*

# RUN git clone https://github.com/ggml-org/llama.cpp.git && \
#     cd llama.cpp && mkdir -p build && cd build && \
#     cmake .. \
#       -DCMAKE_BUILD_TYPE=Release \
#       -DGGML_CUDA=ON \
#       -DGGML_NATIVE=OFF \
#       -DBUILD_SHARED_LIBS=OFF && \
#     cmake --build . --config Release --target llama-server -j"$(nproc)" && \
#     strip ./bin/llama-server

# Runtime-only image; build happens at container start if needed
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04
WORKDIR /app

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 python3-venv python3-distutils python3-pip wget ca-certificates git \
    build-essential cmake ninja-build libcurl4-openssl-dev binutils \
    libcurl4 libgomp1 libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

# copy app files (do NOT include prebuilt binary)
COPY requirements.txt llm.py ollama_llm.py sd.py entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh
CMD ["./entrypoint.sh"]
