# Stage 1: Build llama-server with CUDA support
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

WORKDIR /build

# Install build dependencies (no extra recommends) and binutils for strip
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git build-essential cmake ninja-build libcurl4-openssl-dev binutils ca-certificates wget \
    && rm -rf /var/lib/apt/lists/*

# Clone, compile llama.cpp with CUDA support, strip the binary to reduce size
RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    mkdir -p build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DBUILD_SHARED_LIBS=OFF && \
    cmake --build . --config Release --target llama-server -j$(nproc) && \
    strip ./bin/llama-server && \
    test -f ./bin/llama-server || (echo "llama-server binary not found" && exit 1)

# Stage 2: Minimal runtime image
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

WORKDIR /app

# Install only runtime dependencies (minimal, no git/cmake)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv wget ca-certificates git \
    libcurl4 libgomp1 \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY the compiled llama-server binary from builder stage
COPY --from=builder /build/llama.cpp/build/bin/llama-server /app/llama-server

# Verify the binary exists and is executable 
RUN test -f /app/llama-server && chmod +x /app/llama-server

# Copy application files
COPY requirements.txt /app/
COPY entrypoint.sh /app/
COPY *.py /app/

RUN chmod +x entrypoint.sh

# Create directory structure for mounted volumes
RUN mkdir -p /app/data/models/text /app/data/models/image /app/data/sd

CMD ["./entrypoint.sh"]
