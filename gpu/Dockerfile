FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

WORKDIR /app

# Install Redis client + HTTP client
RUN apt-get update && apt-get install -y \
    python3 python3-pip curl wget && rm -rf /var/lib/apt/lists/*

COPY . /app
RUN chmod +x entrypoint.sh
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 50018

CMD ["./entrypoint.sh"]
