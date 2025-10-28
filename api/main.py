import os
import json
import logging
import time
import uuid
import asyncio
import httpx
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from redis import Redis
import redis.asyncio as redis

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_iso_timestamp():
    """Generate ISO 8601 timestamp in Ollama format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

app = FastAPI(
    title="LLaMA API Service",
    docs_url="/docs",
    redoc_url="/redoc", 
    openapi_url="/openapi.json",
    root_path="/api"
)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASS = os.getenv("REDIS_PASS", "")
A1111_URL = os.getenv("A1111_URL", "http://velesio-gpu:7860")  # Internal container URL
if not os.getenv("REDIS_URL"):
    redis_url = f"redis://:{REDIS_PASS}@{REDIS_HOST}:6379"
redis_pass = os.getenv("REDIS_PASS", None)
redis_conn = Redis.from_url(redis_url, password=redis_pass)
redis_client = redis.from_url(redis_url, password=redis_pass, decode_responses=True)

# Authentication setup
security = HTTPBearer()

# You can set valid tokens via environment variables
# In production, you'd typically validate against a database or external service
VALID_TOKENS = set()
if os.getenv("API_TOKENS"):
    # Comma-separated list of valid tokens
    VALID_TOKENS = set(os.getenv("API_TOKENS").split(","))
    logger.info(f"Loaded {len(VALID_TOKENS)} API tokens from environment")
else:
    logger.warning("No API_TOKENS found in environment variables! API will reject all requests.")
    # No default tokens in production for security

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify the bearer token from the Authorization header.
    Raises HTTPException if token is invalid.
    """
    token = credentials.credentials
    
    if not VALID_TOKENS:
        logger.error("No valid tokens configured. Check API_TOKENS environment variable.")
        raise HTTPException(
            status_code=500,
            detail="Authentication not properly configured",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if token not in VALID_TOKENS:
        logger.warning(f"Invalid token attempt: {token[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Valid token authenticated: {token[:10]}...")
    return token  # Return the validated token

class Prompt(BaseModel):
    text: str

# Unity LLM request models
class ChatRequest(BaseModel):
    prompt: str
    id_slot: Optional[int] = -1
    temperature: Optional[float] = 0.2
    top_k: Optional[int] = 40
    top_p: Optional[float] = 0.9
    min_p: Optional[float] = 0.05
    n_predict: Optional[int] = -1
    n_keep: Optional[int] = -1
    stream: Optional[bool] = True
    stop: Optional[List[str]] = None
    typical_p: Optional[float] = 1.0
    repeat_penalty: Optional[float] = 1.1
    repeat_last_n: Optional[int] = 64
    penalize_nl: Optional[bool] = True
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    penalty_prompt: Optional[str] = None
    mirostat: Optional[int] = 0
    mirostat_tau: Optional[float] = 5.0
    mirostat_eta: Optional[float] = 0.1
    grammar: Optional[str] = None
    seed: Optional[int] = 0
    ignore_eos: Optional[bool] = False
    logit_bias: Optional[Dict[int, str]] = None
    n_probs: Optional[int] = 0
    cache_prompt: Optional[bool] = True

class TokenizeRequest(BaseModel):
    content: str

# Ollama Chat models
class OllamaChatMessage(BaseModel):
    role: str  # system, user, assistant
    content: str
    images: Optional[List[str]] = None  # Base64 encoded images

class OllamaChatRequest(BaseModel):
    model: str
    messages: List[OllamaChatMessage]
    stream: Optional[bool] = False
    format: Optional[str] = None  # json
    options: Optional[Dict[str, Any]] = None
    keep_alive: Optional[Union[str, int]] = None  # Accept both "5m" and 300

# Ollama Generate (completion) model
class OllamaGenerateRequest(BaseModel):
    model: str
    prompt: str
    suffix: Optional[str] = None
    images: Optional[List[str]] = None  # Base64 encoded images for multimodal
    format: Optional[str] = None  # json or JSON schema
    options: Optional[Dict[str, Any]] = None
    system: Optional[str] = None
    template: Optional[str] = None
    stream: Optional[bool] = False
    raw: Optional[bool] = False
    keep_alive: Optional[Union[str, int]] = None  # Accept both "5m" and 300
    context: Optional[List[int]] = None

# Ollama Embeddings model
class OllamaEmbedRequest(BaseModel):
    model: str
    input: Union[str, List[str]]  # Single string or array of strings
    truncate: Optional[bool] = True
    options: Optional[Dict[str, Any]] = None
    keep_alive: Optional[Union[str, int]] = None  # Accept both "5m" and 300

# CompletionRequest - same as ChatRequest but for completion endpoint
class CompletionRequest(BaseModel):
    prompt: str
    id_slot: Optional[int] = -1
    temperature: Optional[float] = 0.2
    top_k: Optional[int] = 40
    top_p: Optional[float] = 0.9
    min_p: Optional[float] = 0.05
    n_predict: Optional[int] = -1
    n_keep: Optional[int] = -1
    stream: Optional[bool] = True
    stop: Optional[List[str]] = None
    typical_p: Optional[float] = 1.0
    repeat_penalty: Optional[float] = 1.1
    repeat_last_n: Optional[int] = 64
    penalize_nl: Optional[bool] = True
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    penalty_prompt: Optional[str] = None
    mirostat: Optional[int] = 0
    mirostat_tau: Optional[float] = 5.0
    mirostat_eta: Optional[float] = 0.1
    grammar: Optional[str] = None
    seed: Optional[int] = 0
    ignore_eos: Optional[bool] = False
    logit_bias: Optional[Dict[int, str]] = None
    n_probs: Optional[int] = 0
    cache_prompt: Optional[bool] = True

class SlotRequest(BaseModel):
    id_slot: int
    filepath: str
    action: str

class SDGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    steps: Optional[int] = 20
    cfg_scale: Optional[float] = 7.0
    width: Optional[int] = 512
    height: Optional[int] = 512
    sampler_name: Optional[str] = "DPM++ 2M Karras"
    seed: Optional[int] = -1
    batch_size: Optional[int] = 1
    n_iter: Optional[int] = 1

# Unity LLM endpoints
@app.get("/props")
async def get_props(token: str = Depends(verify_token)):
    """Get server properties - llama.cpp compatible endpoint"""
    try:
        logger.info("Creating props task for async processing")
        
        # Create task for Redis
        task_data = {
            "endpoint": "props",
            "data": {},
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Props task {task_id} added to Redis queue")
        
        # Wait for result
        result = await wait_for_result(task_id, timeout=30)
        if result.get("error"):
            logger.error(f"Props task error: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"Props result: {result.get('data', {})}")
        return result.get("data", {})
            
    except Exception as e:
        logger.error(f"Error processing props request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing props request: {str(e)}")

@app.get("/template")
async def get_template_get(token: str = Depends(verify_token)):
    """Get the chat template from the LLaMA server via Redis async tasks (GET method)"""
    return await get_template_post(token)

@app.post("/template")
async def get_template_post(token: str = Depends(verify_token)):
    """Get the chat template from the LLaMA server via Redis async tasks (POST method)"""
    try:
        logger.info("Creating template task for async processing")
        
        # Create task for Redis
        task_data = {
            "endpoint": "template",
            "data": {},
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Template task {task_id} added to Redis queue")
        
        # Wait for result
        result = await wait_for_result(task_id, timeout=30)
        if result.get("error"):
            logger.error(f"Template task error: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"Template result: {result.get('data', {})}")
        return result.get("data", {})
            
    except Exception as e:
        logger.error(f"Error processing template request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing template request: {str(e)}")

@app.post("/tokenize")
async def tokenize(request: TokenizeRequest, token: str = Depends(verify_token)):
    """Tokenize text via Redis async tasks"""
    try:
        logger.info(f"Creating tokenize task: {request.content[:50]}...")
        
        # Create task for Redis
        task_data = {
            "endpoint": "tokenize",
            "data": request.dict(),
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Tokenize task {task_id} added to Redis queue")
        
        # Wait for result
        result = await wait_for_result(task_id, timeout=30)
        if result.get("error"):
            logger.error(f"Tokenize task error: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"Tokenize result: {result.get('data', {})}")
        return result.get("data", {})
            
    except Exception as e:
        logger.error(f"Error processing tokenize request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing tokenize request: {str(e)}")

async def wait_for_result(task_id: str, timeout: int = 300):
    """Wait for a result from Redis with timeout"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result_key = f"result:{task_id}"
        result_data = await redis_client.get(result_key)
        
        if result_data:
            result = json.loads(result_data)
            await redis_client.delete(result_key)  # Clean up
            return result
        
        await asyncio.sleep(0.1)  # Check every 100ms
    
    return {"error": "Request timeout"}

async def stream_completion_response(task_id: str):
    """Stream completion response as it arrives from GPU worker"""
    logger.info(f"Starting stream for task {task_id}")
    
    timeout = 300  # 5 minutes timeout
    start_time = time.time()
    chunks_sent = False
    last_chunk_count = 0
    total_tokens_sent = 0
    last_progress_log = 0
    
    while time.time() - start_time < timeout:
        try:
            # Check for streaming updates first (priority for real-time streaming)
            stream_key = f"stream:{task_id}"
            # Get only new chunks since last check
            current_chunk_count = await redis_client.llen(stream_key)
            
            if current_chunk_count > last_chunk_count:
                # Get only the new chunks
                new_chunks = await redis_client.lrange(stream_key, last_chunk_count, current_chunk_count - 1)
                
                if new_chunks:
                    # Process each new streaming chunk immediately
                    for chunk_data in new_chunks:
                        try:
                            chunk = json.loads(chunk_data)
                            chunk_json = json.dumps(chunk)
                            yield f"data: {chunk_json}\n\n"
                            chunks_sent = True
                            total_tokens_sent += 1
                            # Very small delay to ensure proper streaming
                            await asyncio.sleep(0.001)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in stream chunk: {chunk_data}")
                    
                    # Log progress every 50 tokens or every 10 seconds
                    current_time = time.time()
                    if (total_tokens_sent - last_progress_log >= 50) or (current_time - start_time > last_progress_log + 10):
                        logger.info(f"Task {task_id}: streaming progress - {total_tokens_sent} tokens sent, {current_time - start_time:.1f}s elapsed")
                        last_progress_log = total_tokens_sent
                    
                    last_chunk_count = current_chunk_count
            
            # Check for final result
            result_key = f"result:{task_id}"
            result_data = await redis_client.get(result_key)
            
            if result_data:
                result = json.loads(result_data)
                elapsed_time = time.time() - start_time
                logger.info(f"Task {task_id} completed: {total_tokens_sent} tokens, {elapsed_time:.1f}s duration")
                
                if result.get("error"):
                    error_response = {"error": result["error"]}
                    error_json = json.dumps(error_response)
                    yield f"data: {error_json}\n\n"
                else:
                    # Send final stop signal if we sent chunks
                    response_data = result.get("data", {})
                    if chunks_sent and response_data.get("stop", False):
                        # Send final stop signal
                        final_chunk = {
                            "content": "",
                            "multimodal": response_data.get("multimodal", False),
                            "slot_id": response_data.get("slot_id", 0),
                            "stop": True
                        }
                        final_json = json.dumps(final_chunk)
                        yield f"data: {final_json}\n\n"
                    elif not chunks_sent:
                        # No streaming chunks were sent, send the complete result
                        response_json = json.dumps(response_data)
                        yield f"data: {response_json}\n\n"
                
                # Clean up
                await redis_client.delete(result_key)
                await redis_client.delete(stream_key)
                return
            
            await asyncio.sleep(0.05)  # Check every 50ms for new tokens
            
        except Exception as e:
            logger.error(f"Error in stream for task {task_id}: {e}")
            error_response = {"error": f"Streaming error: {str(e)}"}
            error_json = json.dumps(error_response)
            yield f"data: {error_json}\n\n"
            return
    
    # Timeout reached
    logger.error(f"Timeout reached for task {task_id} after {time.time() - start_time:.1f}s")
    timeout_response = {"error": "Request timeout"}
    timeout_json = json.dumps(timeout_response)
    yield f"data: {timeout_json}\n\n"

async def stream_chat_response(task_id: str, model: str):
    """Stream chat response in Ollama format as it arrives from GPU worker"""
    logger.info(f"Starting Ollama chat stream for task {task_id}")
    
    timeout = 300  # 5 minutes timeout
    start_time = time.time()
    chunks_sent = False
    last_chunk_count = 0
    total_tokens_sent = 0
    last_progress_log = 0
    
    while time.time() - start_time < timeout:
        try:
            # Check for streaming updates first
            stream_key = f"stream:{task_id}"
            current_chunk_count = await redis_client.llen(stream_key)
            
            if current_chunk_count > last_chunk_count:
                # Get only the new chunks
                new_chunks = await redis_client.lrange(stream_key, last_chunk_count, current_chunk_count - 1)
                
                if new_chunks:
                    # Process each new streaming chunk immediately
                    for chunk_data in new_chunks:
                        try:
                            chunk = json.loads(chunk_data)
                            # Convert to Ollama chat format
                            ollama_chunk = {
                                "model": model,
                                "created_at": get_iso_timestamp(),
                                "message": {
                                    "role": "assistant",
                                    "content": chunk.get("content", "")
                                },
                                "done": False
                            }
                            chunk_json = json.dumps(ollama_chunk)
                            yield f"{chunk_json}\n"
                            chunks_sent = True
                            total_tokens_sent += 1
                            await asyncio.sleep(0.001)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in stream chunk: {chunk_data}")
                    
                    # Log progress
                    current_time = time.time()
                    if (total_tokens_sent - last_progress_log >= 50) or (current_time - start_time > last_progress_log + 10):
                        logger.info(f"Task {task_id}: streaming progress - {total_tokens_sent} tokens sent, {current_time - start_time:.1f}s elapsed")
                        last_progress_log = total_tokens_sent
                    
                    last_chunk_count = current_chunk_count
            
            # Check for final result
            result_key = f"result:{task_id}"
            result_data = await redis_client.get(result_key)
            
            if result_data:
                result = json.loads(result_data)
                elapsed_time = time.time() - start_time
                logger.info(f"Task {task_id} completed: {total_tokens_sent} tokens, {elapsed_time:.1f}s duration")
                
                if result.get("error"):
                    error_response = {
                        "model": model,
                        "created_at": get_iso_timestamp(),
                        "message": {
                            "role": "assistant",
                            "content": ""
                        },
                        "done": True,
                        "error": result["error"]
                    }
                    yield f"{json.dumps(error_response)}\n"
                else:
                    # Send final done signal
                    response_data = result.get("data", {})
                    final_response = {
                        "model": model,
                        "created_at": get_iso_timestamp(),
                        "message": {
                            "role": "assistant",
                            "content": "" if chunks_sent else response_data.get("content", "")
                        },
                        "done": True,
                        "total_duration": int(elapsed_time * 1e9),  # Convert to nanoseconds
                        "load_duration": response_data.get("load_duration", 0),
                        "prompt_eval_count": response_data.get("prompt_eval_count", 0),
                        "prompt_eval_duration": response_data.get("prompt_eval_duration", 0),
                        "eval_count": response_data.get("eval_count", total_tokens_sent),
                        "eval_duration": response_data.get("eval_duration", 0)
                    }
                    yield f"{json.dumps(final_response)}\n"
                
                # Clean up
                await redis_client.delete(result_key)
                await redis_client.delete(stream_key)
                return
            
            await asyncio.sleep(0.05)  # Check every 50ms for new tokens
            
        except Exception as e:
            logger.error(f"Error in chat stream for task {task_id}: {e}")
            error_response = {
                "model": model,
                "created_at": get_iso_timestamp(),
                "message": {
                    "role": "assistant",
                    "content": ""
                },
                "done": True,
                "error": f"Streaming error: {str(e)}"
            }
            yield f"{json.dumps(error_response)}\n"
            return
    
    # Timeout reached
    logger.error(f"Timeout reached for chat task {task_id} after {time.time() - start_time:.1f}s")
    timeout_response = {
        "model": model,
        "created_at": get_iso_timestamp(),
        "message": {
            "role": "assistant",
            "content": ""
        },
        "done": True,
        "error": "Request timeout"
    }
    yield f"{json.dumps(timeout_response)}\n"

async def stream_generate_response(task_id: str, model: str):
    """Stream generate response in Ollama format as it arrives from GPU worker"""
    logger.info(f"Starting Ollama generate stream for task {task_id}")
    
    timeout = 300  # 5 minutes timeout
    start_time = time.time()
    chunks_sent = False
    last_chunk_count = 0
    total_tokens_sent = 0
    last_progress_log = 0
    
    while time.time() - start_time < timeout:
        try:
            # Check for streaming updates first
            stream_key = f"stream:{task_id}"
            current_chunk_count = await redis_client.llen(stream_key)
            
            if current_chunk_count > last_chunk_count:
                # Get only the new chunks
                new_chunks = await redis_client.lrange(stream_key, last_chunk_count, current_chunk_count - 1)
                
                if new_chunks:
                    # Process each new streaming chunk immediately
                    for chunk_data in new_chunks:
                        try:
                            chunk = json.loads(chunk_data)
                            # Convert to Ollama generate format
                            ollama_chunk = {
                                "model": model,
                                "created_at": get_iso_timestamp(),
                                "response": chunk.get("content", ""),
                                "done": False
                            }
                            chunk_json = json.dumps(ollama_chunk)
                            yield f"{chunk_json}\n"
                            chunks_sent = True
                            total_tokens_sent += 1
                            await asyncio.sleep(0.001)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in stream chunk: {chunk_data}")
                    
                    # Log progress
                    current_time = time.time()
                    if (total_tokens_sent - last_progress_log >= 50) or (current_time - start_time > last_progress_log + 10):
                        logger.info(f"Task {task_id}: streaming progress - {total_tokens_sent} tokens sent, {current_time - start_time:.1f}s elapsed")
                        last_progress_log = total_tokens_sent
                    
                    last_chunk_count = current_chunk_count
            
            # Check for final result
            result_key = f"result:{task_id}"
            result_data = await redis_client.get(result_key)
            
            if result_data:
                result = json.loads(result_data)
                elapsed_time = time.time() - start_time
                logger.info(f"Task {task_id} completed: {total_tokens_sent} tokens, {elapsed_time:.1f}s duration")
                
                if result.get("error"):
                    error_response = {
                        "model": model,
                        "created_at": get_iso_timestamp(),
                        "response": "",
                        "done": True,
                        "error": result["error"]
                    }
                    yield f"{json.dumps(error_response)}\n"
                else:
                    # Send final done signal
                    response_data = result.get("data", {})
                    final_response = {
                        "model": model,
                        "created_at": get_iso_timestamp(),
                        "response": "" if chunks_sent else response_data.get("response", ""),
                        "done": True,
                        "context": response_data.get("context", []),
                        "total_duration": int(elapsed_time * 1e9),  # Convert to nanoseconds
                        "load_duration": response_data.get("load_duration", 0),
                        "prompt_eval_count": response_data.get("prompt_eval_count", 0),
                        "prompt_eval_duration": response_data.get("prompt_eval_duration", 0),
                        "eval_count": response_data.get("eval_count", total_tokens_sent),
                        "eval_duration": response_data.get("eval_duration", 0)
                    }
                    yield f"{json.dumps(final_response)}\n"
                
                # Clean up
                await redis_client.delete(result_key)
                await redis_client.delete(stream_key)
                return
            
            await asyncio.sleep(0.05)  # Check every 50ms for new tokens
            
        except Exception as e:
            logger.error(f"Error in generate stream for task {task_id}: {e}")
            error_response = {
                "model": model,
                "created_at": get_iso_timestamp(),
                "response": "",
                "done": True,
                "error": f"Streaming error: {str(e)}"
            }
            yield f"{json.dumps(error_response)}\n"
            return
    
    # Timeout reached
    logger.error(f"Timeout reached for generate task {task_id} after {time.time() - start_time:.1f}s")
    timeout_response = {
        "model": model,
        "created_at": get_iso_timestamp(),
        "response": "",
        "done": True,
        "error": "Request timeout"
    }
    yield f"{json.dumps(timeout_response)}\n"

@app.post("/chat")
async def chat(request: OllamaChatRequest, token: str = Depends(verify_token)):
    """Handle Ollama-native chat requests with streaming support"""
    logger.info(f"Chat request received for model: {request.model}")
    
    try:
        # Create task for Redis
        task_data = {
            "endpoint": "chat",
            "data": request.dict(),
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Chat task {task_id} added to Redis queue")
        
        # Check if streaming is requested
        if request.stream:
            return StreamingResponse(
                stream_chat_response(task_id, request.model),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Wait for result
            result = await wait_for_result(task_id)
            if result.get("error"):
                raise HTTPException(status_code=500, detail=result["error"])
            return result["data"]
            
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate(request: OllamaGenerateRequest, token: str = Depends(verify_token)):
    """Handle Ollama-native generate/completion requests with streaming support"""
    logger.info(f"Generate request received for model: {request.model}")
    
    try:
        # Create task for Redis
        task_data = {
            "endpoint": "generate",
            "data": request.dict(),
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Generate task {task_id} added to Redis queue")
        
        # Check if streaming is requested
        if request.stream:
            return StreamingResponse(
                stream_generate_response(task_id, request.model),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Wait for result
            result = await wait_for_result(task_id)
            if result.get("error"):
                raise HTTPException(status_code=500, detail=result["error"])
            return result["data"]
            
    except Exception as e:
        logger.error(f"Error in generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tags")
async def list_models(token: str = Depends(verify_token)):
    """List available models from Ollama server"""
    logger.info("List models request received")
    
    try:
        # Create task for Redis
        task_data = {
            "endpoint": "tags",
            "data": {},
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Tags task {task_id} added to Redis queue")
        
        # Wait for result
        result = await wait_for_result(task_id, timeout=30)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        return result["data"]
            
    except Exception as e:
        logger.error(f"Error in tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed")
async def generate_embeddings(request: OllamaEmbedRequest, token: str = Depends(verify_token)):
    """Generate embeddings from a model"""
    logger.info(f"Embed request received for model: {request.model}")
    
    try:
        # Create task for Redis
        task_data = {
            "endpoint": "embed",
            "data": request.dict(),
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Embed task {task_id} added to Redis queue")
        
        # Wait for result (embeddings can take a bit)
        result = await wait_for_result(task_id, timeout=60)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        return result["data"]
            
    except Exception as e:
        logger.error(f"Error in embed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/completion")
async def completion(request: CompletionRequest, token: str = Depends(verify_token)):
    """Handle completion requests with streaming support"""
    logger.info(f"Completion request received: {request.prompt[:50]}...")
    
    try:
        # Create task for Redis
        task_data = {
            "endpoint": "completion",
            "data": request.dict(),
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Task {task_id} added to Redis queue")
        
        # Check if streaming is requested
        if request.stream:
            return StreamingResponse(
                stream_completion_response(task_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering if behind nginx
                }
            )
        else:
            # Wait for result
            result = await wait_for_result(task_id)
            if result.get("error"):
                raise HTTPException(status_code=500, detail=result["error"])
            return result["data"]
            
    except Exception as e:
        logger.error(f"Error in completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/slots")
async def handle_slots(request: SlotRequest, token: str = Depends(verify_token)):
    """Handle slot operations (save/restore cache) via Redis async tasks"""
    try:
        logger.info(f"Creating slots task: {request.dict()}")
        
        # Create task for Redis
        task_data = {
            "endpoint": "slots",
            "data": request.dict(),
            "timestamp": time.time()
        }
        
        # Add to Redis queue
        task_id = str(uuid.uuid4())
        await redis_client.lpush("gpu_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"Slots task {task_id} added to Redis queue")
        
        # Wait for result
        result = await wait_for_result(task_id, timeout=30)
        if result.get("error"):
            logger.error(f"Slots task error: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"Slots result: {result.get('data', {})}")
        return result.get("data", {})
            
    except Exception as e:
        logger.error(f"Error in slots endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in slots: {str(e)}")

@app.post("/generate-image")
async def generate_image(request: SDGenerationRequest, token: str = Depends(verify_token)):
    """Generate images using Stable Diffusion via Redis async tasks"""
    try:
        logger.info(f"SD generation request: {request.prompt[:50]}...")
        
        # Create task for Redis
        task_data = {
            "endpoint": "sd_generation",
            "data": request.dict(),
            "timestamp": time.time()
        }
        
        # Add to Redis queue specifically for SD tasks
        task_id = str(uuid.uuid4())
        await redis_client.lpush("sd_tasks", json.dumps({
            "id": task_id,
            **task_data
        }))
        
        logger.info(f"SD task {task_id} added to Redis sd_tasks queue")
        
        # Wait for result (SD generation can take longer)
        result = await wait_for_result(task_id, timeout=600)  # 10 minute timeout
        if result.get("error"):
            logger.error(f"SD generation error: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"SD generation completed for task {task_id}")
        return result.get("data", {})
            
    except Exception as e:
        logger.error(f"Error in generate-image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

@app.get("/")
def root(token: str = Depends(verify_token)):
    return {
        "message": "LLM API Server", 
        "status": "running",
        "endpoints": {
            "ollama": ["/chat", "/generate", "/tags", "/embed"],
            "llama_cpp": ["/completion", "/template", "/tokenize", "/slots"],
            "stable_diffusion": ["/generate-image", "/sdapi/v1/txt2img", "/sdapi/v1/options"],
            "admin": ["/health"]
        },
        "architecture": "Distributed Redis async task-based worker system",
        "authentication": "Authentication required for all endpoints except /health, use a Bearer token"
    }

@app.get("/health")
def health_check():
    """Health check endpoint that doesn't require authentication"""
    return {"status": "healthy", "timestamp": time.time()}

# A1111 WebUI API Proxy Endpoints for Unity compatibility
@app.get("/sdapi/v1/sd-models")
async def get_sd_models(token: str = Depends(verify_token)):
    """Proxy endpoint for A1111 WebUI sd-models API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{A1111_URL}/sdapi/v1/sd-models", timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying sd-models request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to SD service: {str(e)}")

@app.get("/api/sd-models")  
async def get_sd_models_alt(token: str = Depends(verify_token)):
    """Alternative proxy endpoint for A1111 WebUI sd-models API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{A1111_URL}/sdapi/v1/sd-models", timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying sd-models request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to SD service: {str(e)}")

@app.post("/sdapi/v1/txt2img")
async def txt2img_proxy(request: dict, token: str = Depends(verify_token)):
    """Proxy endpoint for A1111 WebUI txt2img API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{A1111_URL}/sdapi/v1/txt2img", 
                json=request,
                timeout=300.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying txt2img request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

@app.get("/sdapi/v1/options")
async def get_options(token: str = Depends(verify_token)):
    """Proxy endpoint for A1111 WebUI options API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{A1111_URL}/sdapi/v1/options", timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying options request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to SD service: {str(e)}")

@app.post("/sdapi/v1/options")
async def set_options(request: dict, token: str = Depends(verify_token)):
    """Proxy endpoint for A1111 WebUI options API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{A1111_URL}/sdapi/v1/options",
                json=request,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying options request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting options: {str(e)}")


