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
LLAMA_SERVER = os.getenv("LLAMA_SERVER_URL", "http://localhost:1337")

# FastAPI enqueues to this queue via Redis
conn = Redis.from_url(REDIS_URL)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
q = Queue("llama_queue", connection=conn)

def get_template():
    """Get the chat template from the LLaMA server"""
    logger.info("Getting template from LLaMA server")
    try:
        response = requests.post(f"{LLAMA_SERVER}/template", json={}, timeout=30)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Template response: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        return {"error": str(e)}

def tokenize_text(content: str):
    """Tokenize text using LLaMA server"""
    logger.info(f"Tokenizing text: {content[:50]}...")
    try:
        response = requests.post(
            f"{LLAMA_SERVER}/tokenize",
            json={"content": content},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Tokenize response: {result}")
        return result
    except Exception as e:
        logger.error(f"Error tokenizing: {str(e)}")
        return {"error": str(e)}

def handle_completion(request_dict):
    """Handle completion requests from Unity"""
    try:
        logger.info(f"Processing completion request: {request_dict}")
        
        # Convert Unity request to LLaMA.cpp format
        llama_request = {
            "prompt": request_dict["prompt"],
            "id_slot": request_dict.get("id_slot", -1),  # Critical: Pass slot ID for context
            "temperature": request_dict.get("temperature", 0.2),
            "top_k": request_dict.get("top_k", 40),
            "top_p": request_dict.get("top_p", 0.9),
            "min_p": request_dict.get("min_p", 0.05),
            "n_predict": request_dict.get("n_predict", -1),
            "stream": False,  # Use non-streaming for Redis queue
            "repeat_penalty": request_dict.get("repeat_penalty", 1.1),
            "repeat_last_n": request_dict.get("repeat_last_n", 64),
            "penalize_nl": request_dict.get("penalize_nl", True),
            "presence_penalty": request_dict.get("presence_penalty", 0.0),
            "frequency_penalty": request_dict.get("frequency_penalty", 0.0),
            "mirostat": request_dict.get("mirostat", 0),
            "mirostat_tau": request_dict.get("mirostat_tau", 5.0),
            "mirostat_eta": request_dict.get("mirostat_eta", 0.1),
            "seed": request_dict.get("seed", 0),
            "ignore_eos": request_dict.get("ignore_eos", False),
            "n_probs": request_dict.get("n_probs", 0),
            "cache_prompt": request_dict.get("cache_prompt", True)
        }
        
        # Add optional fields if provided
        if request_dict.get("stop"):
            llama_request["stop"] = request_dict["stop"]
        if request_dict.get("grammar"):
            llama_request["grammar"] = request_dict["grammar"]
        if request_dict.get("logit_bias"):
            llama_request["logit_bias"] = request_dict["logit_bias"]
        if request_dict.get("penalty_prompt"):
            llama_request["penalty_prompt"] = request_dict["penalty_prompt"]
        if "n_keep" in request_dict and request_dict["n_keep"] > -1:
            llama_request["n_keep"] = request_dict["n_keep"]
        
        logger.info(f"Sending to LLaMA server: {llama_request}")
        
        # Send request to LLaMA server
        response = requests.post(
            f"{LLAMA_SERVER}/completion",
            json=llama_request,
            timeout=300
        )
        response.raise_for_status()
        
        # Parse JSON response
        result = response.json()
        logger.info(f"LLaMA server response: {result}")
        
        # Convert response for Unity
        unity_result = {
            "content": result.get("content", ""),
            "multimodal": False,
            "slot_id": request_dict.get("id_slot", -1) if request_dict.get("id_slot", -1) >= 0 else 0,
            "stop": result.get("stop", True)
        }
        
        logger.info(f"Returning Unity result: {unity_result}")
        return unity_result
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in completion: {str(e)}")
        return {"error": f"LLaMA server error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in completion endpoint: {str(e)}")
        return {"error": f"Error with completion: {str(e)}"}

def handle_slots(request_dict):
    """Handle slot operations (save/restore cache)"""
    try:
        logger.info(f"Processing slots request: {request_dict}")
        # For now, return a simple response since we don't have cache functionality
        return {"filename": request_dict.get("filepath", "")}
    except Exception as e:
        logger.error(f"Error in slots handler: {str(e)}")
        return {"error": f"Error in slots: {str(e)}"}

async def handle_completion_streaming(request_dict, task_id):
    """Handle streaming completion requests from Unity"""
    try:
        logger.info(f"Processing streaming completion request: {request_dict}")
        
        # Convert Unity request to LLaMA.cpp format
        llama_request = {
            "prompt": request_dict["prompt"],
            "id_slot": request_dict.get("id_slot", -1),
            "temperature": request_dict.get("temperature", 0.2),
            "top_k": request_dict.get("top_k", 40),
            "top_p": request_dict.get("top_p", 0.9),
            "min_p": request_dict.get("min_p", 0.05),
            "n_predict": request_dict.get("n_predict", -1),
            "stream": request_dict.get("stream", True),  # Enable streaming
            "repeat_penalty": request_dict.get("repeat_penalty", 1.1),
            "repeat_last_n": request_dict.get("repeat_last_n", 64),
            "penalize_nl": request_dict.get("penalize_nl", True),
            "presence_penalty": request_dict.get("presence_penalty", 0.0),
            "frequency_penalty": request_dict.get("frequency_penalty", 0.0),
            "mirostat": request_dict.get("mirostat", 0),
            "mirostat_tau": request_dict.get("mirostat_tau", 5.0),
            "mirostat_eta": request_dict.get("mirostat_eta", 0.1),
            "seed": request_dict.get("seed", 0),
            "ignore_eos": request_dict.get("ignore_eos", False),
            "n_probs": request_dict.get("n_probs", 0),
            "cache_prompt": request_dict.get("cache_prompt", True)
        }
        
        # Add optional fields if provided
        if request_dict.get("stop"):
            llama_request["stop"] = request_dict["stop"]
        if request_dict.get("grammar"):
            llama_request["grammar"] = request_dict["grammar"]
        if request_dict.get("logit_bias"):
            llama_request["logit_bias"] = request_dict["logit_bias"]
        if request_dict.get("penalty_prompt"):
            llama_request["penalty_prompt"] = request_dict["penalty_prompt"]
        if "n_keep" in request_dict and request_dict["n_keep"] > -1:
            llama_request["n_keep"] = request_dict["n_keep"]
        
        logger.info(f"Sending streaming request to LLaMA server: {llama_request}")
        
        # Send streaming request to LLaMA server
        response = requests.post(
            f"{LLAMA_SERVER}/completion",
            json=llama_request,
            stream=True,
            timeout=300
        )
        response.raise_for_status()
        
        content = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'content' in data:
                            token_content = data['content']
                            content += token_content
                            # Stream individual token immediately
                            chunk_result = {
                                "content": token_content,
                                "multimodal": False,
                                "slot_id": request_dict.get("id_slot", -1) if request_dict.get("id_slot", -1) >= 0 else 0,
                                "stop": data.get("stop", False)
                            }
                            # Send each token immediately to Redis
                            await redis_client.rpush(f"stream:{task_id}", json.dumps(chunk_result))
                            
                            # Set expiration on the stream key (10 minutes)
                            await redis_client.expire(f"stream:{task_id}", 600)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse streaming data: {data_str}")
        
        # Send final result
        final_result = {
            "content": content,
            "multimodal": False, 
            "slot_id": request_dict.get("id_slot", -1) if request_dict.get("id_slot", -1) >= 0 else 0,
            "stop": True
        }
        
        await redis_client.set(f"result:{task_id}", json.dumps({"data": final_result}), ex=300)
        logger.info(f"Streaming completion finished for task {task_id}")
        
    except requests.exceptions.RequestException as e:
        error_result = {"error": f"LLaMA server error: {str(e)}"}
        await redis_client.set(f"result:{task_id}", json.dumps(error_result), ex=300)
        logger.error(f"Request error in streaming completion: {str(e)}")
    except Exception as e:
        error_result = {"error": f"Error with streaming completion: {str(e)}"}
        await redis_client.set(f"result:{task_id}", json.dumps(error_result), ex=300)
        logger.error(f"Error in streaming completion: {str(e)}")

async def process_gpu_tasks():
    """Process tasks from the gpu_tasks queue"""
    logger.info("Starting GPU task processor...")
    
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

# Add this to make functions available globally for RQ
__all__ = ['call_inference', 'get_template', 'tokenize_text', 'handle_completion', 'handle_slots']

async def main():
    """Main async function to run both RQ worker and GPU task processor"""
    logger.info(f"GPU Worker starting. Connecting to Redis at {REDIS_HOST}")
    logger.info(f"Using LLaMA server at {LLAMA_SERVER}")
    
    # Test Redis connection before starting worker
    try:
        conn.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        exit(1)
    
    # Test async Redis connection
    try:
        await redis_client.ping()
        logger.info("✅ Async Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Async Redis connection failed: {e}")
        exit(1)
    
    # Test LLaMA server connection
    try:
        response = requests.get(f"{LLAMA_SERVER}/health", timeout=10)
        logger.info("✅ LLaMA server connection successful")
    except Exception as e:
        logger.warning(f"⚠️ LLaMA server connection test failed: {e}")
    
    # Start GPU task processor as a background task
    task_processor = asyncio.create_task(process_gpu_tasks())
    
    logger.info("GPU task processor started. For RQ worker, run a separate instance with --rq-only flag")
    
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
