# Build
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder
WORKDIR /build

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git build-essential cmake ninja-build libcurl4-openssl-dev binutils ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/ggml-org/llama.cpp.git && \
    cd llama.cpp && mkdir -p build && cd build && \
    cmake .. \
      -DCMAKE_BUILD_TYPE=Release \
      -DGGML_CUDA=ON \
      -DGGML_NATIVE=OFF \
      -DBUILD_SHARED_LIBS=OFF && \
    cmake --build . --config Release --target llama-server -j"$(nproc)" && \
    strip ./bin/llama-server

# Runtime
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
WORKDIR /app

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libcurl4 libgomp1 ca-certificates pip git \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/llama.cpp/build/bin/llama-server /app/llama-server
RUN chmod +x /app/llama-server

# Copy Python scripts and requirements
COPY requirements.txt llm.py ollama_llm.py sd.py entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh
CMD ["./entrypoint.sh"]
