import os, json, logging, asyncio, requests, base64
from io import BytesIO
from PIL import Image
import redis.asyncio as redis

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASS = os.getenv("REDIS_PASS", "")
REDIS_URL = f"redis://:{REDIS_PASS}@{REDIS_HOST}:6379"
A1111_URL = os.getenv("A1111_URL", "http://localhost:7860")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def handle_sd_generation(request_dict):
    """Handle Stable Diffusion generation requests"""
    try:
        logger.info(f"Processing SD request: {request_dict}")

        # Default payload
        payload = {
            "prompt": "a cat",
            "steps": 20,
            "width": 512,
            "height": 512,
        }
        # Update with provided data
        payload.update(request_dict)

        logger.info(f"Sending to A1111 server: {payload}")

        response = requests.post(url=f'{A1111_URL}/sdapi/v1/txt2img', json=payload, timeout=300)
        response.raise_for_status()
        r = response.json()

        if "images" in r and r["images"]:
            image_data = r['images'][0]
            # The result is a base64 encoded string
            return {"image_base64": image_data}
        else:
            return {"error": "No images returned from A1111"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in SD generation: {str(e)}")
        return {"error": f"A1111 server error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in SD generation: {str(e)}")
        return {"error": f"Error with SD generation: {str(e)}"}

async def process_sd_tasks():
    """Process tasks from the sd_tasks queue"""
    logger.info("Starting SD task processor...")

    while True:
        try:
            task_data = await redis_client.brpop("sd_tasks", timeout=1)
            if task_data:
                task_json = task_data[1]
                task = json.loads(task_json)
                task_id = task["id"]
                request_data = task["data"]

                logger.info(f"Processing task {task_id} for SD generation")

                result = await handle_sd_generation(request_data)
                await redis_client.set(f"result:{task_id}", json.dumps({"data": result}), ex=600)
        except asyncio.CancelledError:
            logger.info("SD task processor cancelled.")
            break
        except Exception as e:
            logger.error(f"Error processing SD task: {e}")
            await asyncio.sleep(1)

    logger.info("SD task processor stopped")

async def main():
    """Main async function to run the SD task processor"""
    logger.info(f"SD Worker starting. Connecting to Redis at {REDIS_HOST}")
    logger.info(f"Using A1111 server at {A1111_URL}")

    try:
        await redis_client.ping()
        logger.info("✅ Async Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Async Redis connection failed: {e}")
        return

    try:
        response = requests.get(f"{A1111_URL}/docs", timeout=10)
        if response.status_code == 200:
            logger.info("✅ A1111 server connection successful")
        else:
            logger.warning(f"⚠️ A1111 server connection test returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ A1111 server connection test failed: {e}")

    await process_sd_tasks()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("SD worker stopped by user.")
