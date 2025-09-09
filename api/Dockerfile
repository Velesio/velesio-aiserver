# Use a slim Python base
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system deps for Redis client
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     build-essential \
  && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose FastAPI port
EXPOSE 8000

# Launch Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
