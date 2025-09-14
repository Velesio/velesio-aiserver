---
layout: page
title: Troubleshooting
nav_order: 6
---

# Troubleshooting Guide

Common issues and their solutions when running Graycat AI Server.

## Quick Diagnostics

Start with these commands to check system status:

```bash
# Check all services
docker-compose ps

# Check logs for errors
docker-compose logs --tail=50

# Check GPU availability
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# Test API health
curl http://localhost:8000/health
```

## Installation Issues

### Docker GPU Runtime Not Found

**Error**: `could not select device driver "" with capabilities: [[gpu]]`

**Solution**:
```bash
# Install NVIDIA Docker runtime
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

### Model Download Failures

**Error**: `Failed to download model from URL`

**Symptoms**:
- Container logs show download errors
- Models directory is empty
- Workers fail to start

**Solutions**:

1. **Check Internet Connection**:
   ```bash
   # Test from container
   docker run --rm alpine ping -c 4 huggingface.co
   ```

2. **Manual Model Download**:
   ```bash
   # Download models manually
   cd gpu/data/models/text
   wget https://huggingface.co/your-model/resolve/main/model.gguf
   
   cd ../image/models/Stable-diffusion
   wget https://huggingface.co/your-sd-model/resolve/main/model.safetensors
   ```

3. **Check Disk Space**:
   ```bash
   df -h
   # Ensure sufficient space (models can be 4-20GB)
   ```

4. **Verify Model URLs**:
   ```bash
   # Test URL accessibility
   curl -I $MODEL_URL
   ```

### Permission Issues

**Error**: `Permission denied` or `Operation not permitted`

**Solution**:
```bash
# Fix ownership of data directory
sudo chown -R $(id -u):$(id -g) gpu/data/

# Fix permissions
chmod -R 755 gpu/data/

# For SELinux systems
sudo setsebool -P container_manage_cgroup true
```

## Runtime Issues

### API Returns 401 Unauthorized

**Symptoms**:
- All API calls return 401
- Authentication header is provided

**Solutions**:

1. **Check API Token Configuration**:
   ```bash
   # Verify environment variable
   docker-compose exec api env | grep API_TOKENS
   
   # Check if token matches
   echo "your-token-here" | base64
   ```

2. **Verify Bearer Token Format**:
   ```bash
   # Correct format
   curl -H "Authorization: Bearer your-token-here" http://localhost:8000/health
   
   # NOT: "Authorization: your-token-here"
   ```

3. **Check Token in Environment File**:
   ```bash
   # In .env file
   API_TOKENS=token1,token2,token3
   # No spaces around commas
   ```

### Workers Not Processing Jobs

**Symptoms**:
- API accepts requests but returns timeouts
- Queue depth increases continuously
- No worker activity in logs

**Diagnostics**:
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Check queue status
docker-compose exec redis redis-cli LLEN llama_queue

# Check worker logs
docker-compose logs graycat-gpu
```

**Solutions**:

1. **Restart Workers**:
   ```bash
   docker-compose restart graycat-gpu
   ```

2. **Check Worker Configuration**:
   ```bash
   # Verify worker environment
   docker-compose exec graycat-gpu env | grep REDIS
   ```

3. **Clear Stuck Jobs**:
   ```bash
   # Clear Redis queue
   docker-compose exec redis redis-cli FLUSHDB
   ```

### GPU Out of Memory

**Error**: `CUDA out of memory` or `RuntimeError: CUDA error: out of memory`

**Solutions**:

1. **Reduce GPU Layers**:
   ```bash
   # In .env file
   GPU_LAYERS=20  # Reduce from default 35
   ```

2. **Use Smaller Model**:
   ```bash
   # Switch to quantized model
   MODEL_URL=https://huggingface.co/model-q4_k_m.gguf
   ```

3. **Reduce Batch Size**:
   ```bash
   # For Stable Diffusion
   SD_BATCH_SIZE=1
   ```

4. **Check GPU Memory**:
   ```bash
   # Monitor GPU usage
   watch -n 1 nvidia-smi
   ```

### Slow Inference Speed

**Symptoms**:
- Text generation takes >30 seconds
- Image generation takes >5 minutes

**Solutions**:

1. **Optimize GPU Layers**:
   ```bash
   # Increase GPU layers if memory allows
   GPU_LAYERS=40
   ```

2. **Check CPU Usage**:
   ```bash
   # If GPU_LAYERS is low, CPU becomes bottleneck
   htop
   ```

3. **Use Flash Attention**:
   ```bash
   # For Stable Diffusion
   SD_FLASH_ATTENTION=true
   ```

4. **Model Optimization**:
   ```bash
   # Use optimized model formats
   # GGUF with Q4_K_M quantization for LLM
   # SafeTensors for Stable Diffusion
   ```

## Service-Specific Issues

### Redis Connection Issues

**Error**: `ConnectionError: Error connecting to Redis`

**Solutions**:

1. **Check Redis Service**:
   ```bash
   docker-compose ps redis
   docker-compose logs redis
   ```

2. **Test Redis Connectivity**:
   ```bash
   # From within network
   docker-compose exec api ping redis
   
   # Test Redis directly
   docker-compose exec redis redis-cli ping
   ```

3. **Check Port Binding**:
   ```bash
   # Verify Redis port
   netstat -tlnp | grep 6379
   ```

### FastAPI Service Issues

**Error**: `502 Bad Gateway` or API not responding

**Solutions**:

1. **Check API Service Health**:
   ```bash
   docker-compose logs api
   curl http://localhost:8000/health
   ```

2. **Verify Port Binding**:
   ```bash
   docker-compose ps api
   netstat -tlnp | grep 8000
   ```

3. **Check Resource Usage**:
   ```bash
   docker stats
   ```

### Stable Diffusion Issues

**Error**: Stable Diffusion worker fails to start

**Solutions**:

1. **Check SD Dependencies**:
   ```bash
   # Verify CUDA version compatibility
   docker-compose exec graycat-gpu nvidia-smi
   ```

2. **Disable SD if Not Needed**:
   ```bash
   # In .env file
   RUN_SD=false
   ```

3. **Check SD Model Loading**:
   ```bash
   # SD worker logs
   docker-compose logs graycat-gpu | grep -i "stable"
   ```

## Network Issues

### Cannot Access API from External Host

**Solutions**:

1. **Check Firewall**:
   ```bash
   # Allow API port
   sudo ufw allow 8000
   
   # Check iptables
   sudo iptables -L
   ```

2. **Verify Docker Port Binding**:
   ```bash
   # Should show 0.0.0.0:8000
   docker port graycat-api
   ```

3. **Test from Different Network**:
   ```bash
   # From external host
   curl http://your-server-ip:8000/health
   ```

### SSL/TLS Issues

**Error**: Certificate verification failed

**Solutions**:

1. **Check Certificate**:
   ```bash
   # Verify certificate chain
   openssl s_client -connect your-domain.com:443 -servername your-domain.com
   ```

2. **Update Nginx Configuration**:
   ```nginx
   # In nginx.conf
   ssl_certificate /etc/nginx/ssl/fullchain.pem;
   ssl_certificate_key /etc/nginx/ssl/privkey.pem;
   ```

## Performance Issues

### High Memory Usage

**Solutions**:

1. **Monitor Memory Usage**:
   ```bash
   # Check container memory
   docker stats
   
   # Check host memory
   free -h
   ```

2. **Reduce Model Context**:
   ```bash
   # Limit context length
   MAX_CONTEXT_LENGTH=2048
   ```

3. **Implement Memory Cleanup**:
   ```bash
   # Clear model cache periodically
   docker-compose exec graycat-gpu pkill -f undreamai_server
   ```

### Queue Backup

**Symptoms**:
- Requests pile up in queue
- Response times increase

**Solutions**:

1. **Scale Workers**:
   ```bash
   # Add more worker containers
   docker-compose up -d --scale graycat-gpu=3
   ```

2. **Implement Rate Limiting**:
   ```nginx
   # In nginx.conf
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
   ```

3. **Monitor Queue Depth**:
   ```bash
   # Check queue status
   curl http://localhost:8000/queue/status
   ```

## Monitoring and Debugging

### Enable Debug Logging

```bash
# In .env file
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

### Health Check Script

Create `scripts/health-check.sh`:

```bash
#!/bin/bash

echo "=== Graycat AI Server Health Check ==="

# Check Docker
if ! docker --version >/dev/null 2>&1; then
    echo "❌ Docker not installed or not running"
    exit 1
fi

# Check GPU
if ! docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi >/dev/null 2>&1; then
    echo "❌ GPU not accessible from Docker"
    exit 1
fi

# Check services
echo "📋 Service Status:"
docker-compose ps

# Check API health
echo "🔍 API Health:"
curl -s http://localhost:8000/health | jq . || echo "❌ API not responding"

# Check Redis
echo "🔍 Redis Status:"
docker-compose exec -T redis redis-cli ping || echo "❌ Redis not responding"

# Check GPU memory
echo "🎮 GPU Status:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits

echo "✅ Health check complete"
```

### Log Analysis

```bash
# Find errors in logs
docker-compose logs --since="1h" | grep -i error

# Monitor real-time logs
docker-compose logs -f | grep -E "(error|exception|failed)"

# Analyze API response times
docker-compose logs api | grep "completion_request" | tail -100
```

## Getting Help

### Debug Information to Collect

When seeking help, provide:

1. **System Information**:
   ```bash
   # OS and version
   cat /etc/os-release
   
   # Docker version
   docker --version
   docker-compose --version
   
   # GPU information
   nvidia-smi
   ```

2. **Service Status**:
   ```bash
   docker-compose ps
   docker-compose logs --tail=100
   ```

3. **Configuration**:
   ```bash
   # Environment (remove sensitive data)
   cat .env | sed 's/API_TOKENS=.*/API_TOKENS=***REDACTED***/'
   ```

4. **Error Messages**: Full error messages and stack traces

### Community Support

- **GitHub Issues**: https://github.com/GrayCatHQ/graycat-aiserver/issues
- **Documentation**: This documentation site
- **Discord**: Join our community Discord server

### Enterprise Support

For production deployments and enterprise support:
- Email: support@graycathq.com
- Priority support available for enterprise customers

## Preventive Measures

### Regular Maintenance

```bash
# Weekly maintenance script
#!/bin/bash

# Clean up old containers
docker system prune -f

# Update images
docker-compose pull

# Restart services
docker-compose down && docker-compose up -d

# Check disk space
df -h

# Verify GPU health
nvidia-smi
```

### Monitoring Setup

Set up alerts for:
- High GPU memory usage (>90%)
- Queue depth (>10 jobs)
- API response time (>30 seconds)
- Disk space (>80% full)
- Service downtime

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash

# Backup configuration
cp .env /backups/env-$(date +%Y%m%d).backup

# Backup Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb /backups/redis-$(date +%Y%m%d).rdb

# Backup models (if custom)
tar -czf /backups/models-$(date +%Y%m%d).tar.gz gpu/data/models/
```

---

Still having issues? Check our [GitHub Issues](https://github.com/GrayCatHQ/graycat-aiserver/issues) or contact support.