import os, time, requests, json, logging, asyncio
from redis import Redis
import redis.asyncio as redis
from rq import Worker, Queue, Connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASS = os.getenv("REDIS_PASS", "")
REDIS_URL = f"redis://:{REDIS_PASS}@{REDIS_HOST}:6379"
OLLAMA_SERVER = os.getenv("OLLAMA_SERVER_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

# FastAPI enqueues to this queue via Redis
conn = Redis.from_url(REDIS_URL)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
q = Queue("llama_queue", connection=conn)

def get_template():
    """Get the chat template - Ollama doesn't have a template endpoint, so return a default"""
    logger.info("Getting template (Ollama mode)")
    try:
        return {
            "chat_template": "default",
            "model": OLLAMA_MODEL
        }
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        return {"error": str(e)}

def tokenize_text(content: str):
    """Tokenize text using Ollama - approximate token count"""
    logger.info(f"Tokenizing text: {content[:50]}...")
    try:
        # Ollama doesn't have a tokenize endpoint, approximate with character count
        # Rough estimate: 1 token ≈ 4 characters
        tokens = [i for i in range(len(content) // 4)]
        return {"tokens": tokens}
    except Exception as e:
        logger.error(f"Error tokenizing: {str(e)}")
        return {"error": str(e)}

def handle_completion(request_dict):
    """Handle completion requests from Unity, converting to Ollama format"""
    try:
        logger.info(f"Processing Ollama completion request: {request_dict}")
        
        # Convert Unity/LLaMA.cpp request to Ollama format
        ollama_request = {
            "model": request_dict.get("model", OLLAMA_MODEL),
            "prompt": request_dict["prompt"],
            "stream": False,
            "options": {
                "temperature": request_dict.get("temperature", 0.2),
                "top_k": request_dict.get("top_k", 40),
                "top_p": request_dict.get("top_p", 0.9),
                "repeat_penalty": request_dict.get("repeat_penalty", 1.1),
                "seed": request_dict.get("seed", 0),
                "num_predict": request_dict.get("n_predict", -1),
            }
        }
        
        # Add stop sequences if provided
        if request_dict.get("stop"):
            stop_sequences = request_dict["stop"]
            if isinstance(stop_sequences, str):
                stop_sequences = [stop_sequences]
            ollama_request["options"]["stop"] = stop_sequences
        
        logger.info(f"Sending to Ollama server: {ollama_request}")
        
        # Send request to Ollama server
        response = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json=ollama_request,
            timeout=300
        )
        response.raise_for_status()
        
        # Parse JSON response
        result = response.json()
        logger.info(f"Ollama server response: {result}")
        
        # Convert response for Unity (matching LLaMA.cpp format)
        unity_result = {
            "content": result.get("response", ""),
            "multimodal": False,
            "slot_id": request_dict.get("id_slot", -1) if request_dict.get("id_slot", -1) >= 0 else 0,
            "stop": result.get("done", True)
        }
        
        logger.info(f"Returning Unity result: {unity_result}")
        return unity_result
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in completion: {str(e)}")
        return {"error": f"Ollama server error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in completion endpoint: {str(e)}")
        return {"error": f"Error with completion: {str(e)}"}

def handle_chat(request_dict):
    """Handle Ollama-native chat requests"""
    try:
        logger.info(f"Processing Ollama chat request: {request_dict}")
        
        # Request is already in Ollama format, pass through
        ollama_request = {
            "model": request_dict.get("model", OLLAMA_MODEL),
            "messages": request_dict["messages"],
            "stream": False
        }
        
        # Add optional parameters
        if request_dict.get("format"):
            ollama_request["format"] = request_dict["format"]
        if request_dict.get("options"):
            ollama_request["options"] = request_dict["options"]
        if request_dict.get("keep_alive"):
            ollama_request["keep_alive"] = request_dict["keep_alive"]
        if request_dict.get("tools"):
            ollama_request["tools"] = request_dict["tools"]
        
        logger.info(f"Sending to Ollama server: {ollama_request}")
        
        # Send request to Ollama server
        response = requests.post(
            f"{OLLAMA_SERVER}/api/chat",
            json=ollama_request,
            timeout=300
        )
        response.raise_for_status()
        
        # Return response in Ollama format
        result = response.json()
        logger.info(f"Ollama chat response: {result}")
        return result
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in chat: {str(e)}")
        return {"error": f"Ollama server error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {"error": f"Error with chat: {str(e)}"}

def handle_generate(request_dict):
    """Handle Ollama-native generate/completion requests"""
    try:
        logger.info(f"Processing Ollama generate request: {request_dict}")
        
        # Request is already in Ollama format, pass through
        ollama_request = {
            "model": request_dict.get("model", OLLAMA_MODEL),
            "prompt": request_dict["prompt"],
            "stream": False
        }
        
        # Add optional parameters
        if request_dict.get("suffix"):
            ollama_request["suffix"] = request_dict["suffix"]
        if request_dict.get("images"):
            ollama_request["images"] = request_dict["images"]
        if request_dict.get("format"):
            ollama_request["format"] = request_dict["format"]
        if request_dict.get("options"):
            ollama_request["options"] = request_dict["options"]
        if request_dict.get("system"):
            ollama_request["system"] = request_dict["system"]
        if request_dict.get("template"):
            ollama_request["template"] = request_dict["template"]
        if request_dict.get("raw"):
            ollama_request["raw"] = request_dict["raw"]
        if request_dict.get("keep_alive"):
            ollama_request["keep_alive"] = request_dict["keep_alive"]
        if request_dict.get("context"):
            ollama_request["context"] = request_dict["context"]
        
        logger.info(f"Sending to Ollama server: {ollama_request}")
        
        # Send request to Ollama server
        response = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json=ollama_request,
            timeout=300
        )
        response.raise_for_status()
        
        # Return response in Ollama format
        result = response.json()
        logger.info(f"Ollama generate response: {result}")
        return result
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in generate: {str(e)}")
        return {"error": f"Ollama server error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        return {"error": f"Error with generate: {str(e)}"}

def handle_tags():
    """List available models from Ollama server"""
    try:
        logger.info("Processing tags (list models) request")
        
        # Send request to Ollama server
        response = requests.get(
            f"{OLLAMA_SERVER}/api/tags",
            timeout=30
        )
        response.raise_for_status()
        
        # Return response in Ollama format
        result = response.json()
        logger.info(f"Ollama tags response: {len(result.get('models', []))} models")
        return result
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in tags: {str(e)}")
        return {"error": f"Ollama server error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in tags endpoint: {str(e)}")
        return {"error": f"Error with tags: {str(e)}"}

def handle_embed(request_dict):
    """Handle embeddings generation requests"""
    try:
        logger.info(f"Processing Ollama embed request: {request_dict}")
        
        # Request is already in Ollama format, pass through
        ollama_request = {
            "model": request_dict.get("model", OLLAMA_MODEL),
            "input": request_dict["input"]
        }
        
        # Add optional parameters
        if "truncate" in request_dict:
            ollama_request["truncate"] = request_dict["truncate"]
        if request_dict.get("options"):
            ollama_request["options"] = request_dict["options"]
        if request_dict.get("keep_alive"):
            ollama_request["keep_alive"] = request_dict["keep_alive"]
        
        logger.info(f"Sending to Ollama server: {ollama_request}")
        
        # Send request to Ollama server
        response = requests.post(
            f"{OLLAMA_SERVER}/api/embed",
            json=ollama_request,
            timeout=60
        )
        response.raise_for_status()
        
        # Return response in Ollama format
        result = response.json()
        logger.info(f"Ollama embed response: {len(result.get('embeddings', []))} embeddings")
        return result
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in embed: {str(e)}")
        return {"error": f"Ollama server error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in embed endpoint: {str(e)}")
        return {"error": f"Error with embed: {str(e)}"}

async def handle_generate_streaming(request_dict, task_id):
    """Handle streaming Ollama generate requests"""
    try:
        logger.info(f"Processing streaming Ollama generate request: {request_dict}")
        
        # Request is already in Ollama format
        ollama_request = {
            "model": request_dict.get("model", OLLAMA_MODEL),
            "prompt": request_dict["prompt"],
            "stream": True
        }
        
        # Add optional parameters
        if request_dict.get("suffix"):
            ollama_request["suffix"] = request_dict["suffix"]
        if request_dict.get("images"):
            ollama_request["images"] = request_dict["images"]
        if request_dict.get("format"):
            ollama_request["format"] = request_dict["format"]
        if request_dict.get("options"):
            ollama_request["options"] = request_dict["options"]
        if request_dict.get("system"):
            ollama_request["system"] = request_dict["system"]
        if request_dict.get("template"):
            ollama_request["template"] = request_dict["template"]
        if request_dict.get("raw"):
            ollama_request["raw"] = request_dict["raw"]
        if request_dict.get("keep_alive"):
            ollama_request["keep_alive"] = request_dict["keep_alive"]
        if request_dict.get("context"):
            ollama_request["context"] = request_dict["context"]
        
        logger.info(f"Sending streaming generate request to Ollama: {ollama_request}")
        
        # Send streaming request to Ollama server
        response = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json=ollama_request,
            stream=True,
            timeout=300
        )
        response.raise_for_status()
        
        # Stream the response tokens back through Redis
        token_count = 0
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    
                    # Extract response content for streaming
                    content = chunk.get("response", "")
                    
                    if content:
                        # Push token to Redis stream
                        stream_chunk = {
                            "content": content
                        }
                        await redis_client.rpush(f"stream:{task_id}", json.dumps(stream_chunk))
                        token_count += 1
                    
                    # Check if this is the final chunk
                    if chunk.get("done", False):
                        logger.info(f"Ollama generate streaming complete: {token_count} tokens")
                        # Store final result with metadata
                        final_result = {
                            "response": "",  # Content already streamed
                            "context": chunk.get("context", []),
                            "total_duration": chunk.get("total_duration", 0),
                            "load_duration": chunk.get("load_duration", 0),
                            "prompt_eval_count": chunk.get("prompt_eval_count", 0),
                            "prompt_eval_duration": chunk.get("prompt_eval_duration", 0),
                            "eval_count": chunk.get("eval_count", token_count),
                            "eval_duration": chunk.get("eval_duration", 0)
                        }
                        await redis_client.set(
                            f"result:{task_id}",
                            json.dumps({"data": final_result}),
                            ex=300
                        )
                        break
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse streaming chunk: {e}")
                    continue
        
        logger.info(f"Ollama generate streaming completed for task {task_id}")
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama server error during streaming: {str(e)}"
        logger.error(error_msg)
        await redis_client.set(
            f"result:{task_id}",
            json.dumps({"error": error_msg}),
            ex=300
        )
    except Exception as e:
        error_msg = f"Error in generate streaming: {str(e)}"
        logger.error(error_msg)
        await redis_client.set(
            f"result:{task_id}",
            json.dumps({"error": error_msg}),
            ex=300
        )

async def handle_chat_streaming(request_dict, task_id):
    """Handle streaming Ollama chat requests"""
    try:
        logger.info(f"Processing streaming Ollama chat request: {request_dict}")
        
        # Request is already in Ollama format
        ollama_request = {
            "model": request_dict.get("model", OLLAMA_MODEL),
            "messages": request_dict["messages"],
            "stream": True
        }
        
        # Add optional parameters
        if request_dict.get("format"):
            ollama_request["format"] = request_dict["format"]
        if request_dict.get("options"):
            ollama_request["options"] = request_dict["options"]
        if request_dict.get("keep_alive"):
            ollama_request["keep_alive"] = request_dict["keep_alive"]
        if request_dict.get("tools"):
            ollama_request["tools"] = request_dict["tools"]
        
        logger.info(f"Sending streaming chat request to Ollama: {ollama_request}")
        
        # Send streaming request to Ollama server
        response = requests.post(
            f"{OLLAMA_SERVER}/api/chat",
            json=ollama_request,
            stream=True,
            timeout=300
        )
        response.raise_for_status()
        
        # Stream the response tokens back through Redis
        token_count = 0
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    
                    # Extract message content for streaming
                    message = chunk.get("message", {})
                    content = message.get("content", "")
                    
                    if content:
                        # Push token to Redis stream
                        stream_chunk = {
                            "content": content,
                            "role": message.get("role", "assistant")
                        }
                        await redis_client.rpush(f"stream:{task_id}", json.dumps(stream_chunk))
                        token_count += 1
                    
                    # Check if this is the final chunk
                    if chunk.get("done", False):
                        logger.info(f"Ollama chat streaming complete: {token_count} tokens")
                        # Store final result with metadata
                        final_result = {
                            "content": "",  # Content already streamed
                            "total_duration": chunk.get("total_duration", 0),
                            "load_duration": chunk.get("load_duration", 0),
                            "prompt_eval_count": chunk.get("prompt_eval_count", 0),
                            "prompt_eval_duration": chunk.get("prompt_eval_duration", 0),
                            "eval_count": chunk.get("eval_count", token_count),
                            "eval_duration": chunk.get("eval_duration", 0)
                        }
                        await redis_client.set(
                            f"result:{task_id}",
                            json.dumps({"data": final_result}),
                            ex=300
                        )
                        break
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse streaming chunk: {e}")
                    continue
        
        logger.info(f"Ollama chat streaming completed for task {task_id}")
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama server error during streaming: {str(e)}"
        logger.error(error_msg)
        await redis_client.set(
            f"result:{task_id}",
            json.dumps({"error": error_msg}),
            ex=300
        )
    except Exception as e:
        error_msg = f"Error in chat streaming: {str(e)}"
        logger.error(error_msg)
        await redis_client.set(
            f"result:{task_id}",
            json.dumps({"error": error_msg}),
            ex=300
        )

def handle_slots(request_dict):
    """Handle slot operations (save/restore cache) - Ollama doesn't support this"""
    try:
        logger.info(f"Processing slots request (Ollama mode - not supported): {request_dict}")
        # Return a simple response since Ollama doesn't have cache functionality
        return {"filename": request_dict.get("filepath", ""), "note": "Ollama mode: caching not supported"}
    except Exception as e:
        logger.error(f"Error in slots handler: {str(e)}")
        return {"error": f"Error in slots: {str(e)}"}

async def handle_completion_streaming(request_dict, task_id):
    """Handle streaming completion requests from Unity"""
    try:
        logger.info(f"Processing streaming Ollama completion request: {request_dict}")
        
        # Convert Unity request to Ollama format with streaming
        ollama_request = {
            "model": request_dict.get("model", OLLAMA_MODEL),
            "prompt": request_dict["prompt"],
            "stream": True,
            "options": {
                "temperature": request_dict.get("temperature", 0.2),
                "top_k": request_dict.get("top_k", 40),
                "top_p": request_dict.get("top_p", 0.9),
                "repeat_penalty": request_dict.get("repeat_penalty", 1.1),
                "seed": request_dict.get("seed", 0),
                "num_predict": request_dict.get("n_predict", -1),
            }
        }
        
        # Add stop sequences if provided
        if request_dict.get("stop"):
            stop_sequences = request_dict["stop"]
            if isinstance(stop_sequences, str):
                stop_sequences = [stop_sequences]
            ollama_request["options"]["stop"] = stop_sequences
        
        logger.info(f"Sending streaming request to Ollama: {ollama_request}")
        
        # Send streaming request to Ollama server
        response = requests.post(
            f"{OLLAMA_SERVER}/api/generate",
            json=ollama_request,
            stream=True,
            timeout=300
        )
        response.raise_for_status()
        
        # Store the stream key in Redis for client polling
        stream_key = f"stream:{task_id}"
        
        # Process the streaming response
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    
                    # Store chunk in Redis
                    await redis_client.rpush(stream_key, json.dumps(chunk))
                    await redis_client.expire(stream_key, 300)  # 5 min TTL
                    
                    if chunk.get("done", False):
                        logger.info(f"Streaming completed for task {task_id}")
                        break
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse streaming chunk: {e}")
                    continue
        
        # Mark as complete
        await redis_client.set(f"stream:{task_id}:complete", "true", ex=300)
        
        return {"status": "streaming_complete", "task_id": task_id}
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in streaming completion: {str(e)}")
        await redis_client.set(f"stream:{task_id}:error", str(e), ex=300)
        return {"error": f"Ollama streaming error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in streaming completion: {str(e)}")
        await redis_client.set(f"stream:{task_id}:error", str(e), ex=300)
        return {"error": f"Error with streaming: {str(e)}"}

async def process_gpu_tasks():
    """Process tasks from the gpu_tasks queue"""
    logger.info("Starting Ollama GPU task processor...")
    
    while True:
        try:
            # Check for new tasks
            task_data = await redis_client.brpop("gpu_tasks", timeout=1)
            if task_data:
                task_json = task_data[1]
                task = json.loads(task_json)
                task_id = task["id"]
                endpoint = task["endpoint"]
                request_data = task["data"]
                
                logger.info(f"Processing task {task_id} for endpoint {endpoint}")
                
                if endpoint == "completion":
                    if request_data.get("stream", True):
                        await handle_completion_streaming(request_data, task_id)
                    else:
                        # Handle non-streaming completion
                        result = handle_completion(request_data)
                        await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=300)
                elif endpoint == "chat":
                    if request_data.get("stream", False):
                        await handle_chat_streaming(request_data, task_id)
                    else:
                        # Handle non-streaming chat
                        result = handle_chat(request_data)
                        await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=300)
                elif endpoint == "generate":
                    if request_data.get("stream", False):
                        await handle_generate_streaming(request_data, task_id)
                    else:
                        # Handle non-streaming generate
                        result = handle_generate(request_data)
                        await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=300)
                elif endpoint == "tags":
                    # Handle tags (list models) request
                    result = handle_tags()
                    await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=300)
                elif endpoint == "embed":
                    # Handle embeddings request
                    result = handle_embed(request_data)
                    await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=300)
                elif endpoint == "template":
                    # Handle template request
                    result = get_template()
                    await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=300)
                elif endpoint == "tokenize":
                    # Handle tokenize request
                    result = tokenize_text(request_data["content"])
                    await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=300)
                elif endpoint == "slots":
                    # Handle slots request
                    result = handle_slots(request_data)
                    await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=300)
                else:
                    logger.warning(f"Unknown endpoint: {endpoint}")
                    await redis_client.set(f"result:{task_id}", json.dumps({"error": f"Unknown endpoint: {endpoint}"}), ex=300)
        
        except Exception as e:
            logger.error(f"Error processing GPU task: {e}")
            await asyncio.sleep(1)
            
    logger.info("GPU task processor stopped")

async def main():
    """Main entry point"""
    logger.info(f"🦙 Ollama LLM Worker starting. Connecting to Redis at {REDIS_HOST}")
    logger.info(f"🦙 Using Ollama server at {OLLAMA_SERVER}")
    logger.info(f"🦙 Default model: {OLLAMA_MODEL}")
    
    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info("✅ Async Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Async Redis connection failed: {e}")
        exit(1)
    
    # Test Ollama server connection
    try:
        response = requests.get(f"{OLLAMA_SERVER}/api/tags", timeout=10)
        logger.info(f"✅ Ollama server connection successful: {response.json()}")
    except Exception as e:
        logger.warning(f"⚠️ Ollama server connection test failed: {e}")
    
    # Start GPU task processor as a background task
    task_processor = asyncio.create_task(process_gpu_tasks())
    
    logger.info("Ollama GPU task processor started. For RQ worker, run a separate instance with --rq-only flag")
    
    # Wait for the task processor
    await task_processor

def run_rq_only():
    """Run only the RQ worker - for separate process"""
    logger.info(f"RQ-only Worker starting. Connecting to Redis at {REDIS_HOST}")
    
    try:
        conn.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        exit(1)
    
    with Connection(conn):
        worker = Worker(["llama_queue"], connection=conn)
        logger.info("RQ Worker ready to process jobs from queue 'llama_queue'")
        worker.work()

if __name__ == "__main__":
    import sys
    
    # Check for RQ-only flag
    if "--rq-only" in sys.argv:
        run_rq_only()
    else:
        asyncio.run(main())
