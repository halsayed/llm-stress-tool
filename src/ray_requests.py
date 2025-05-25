import time
from typing import Dict, Any

import aiohttp
import ray


@ray.remote
async def make_request(base_url: str, headers: Dict[str, str], model_name: str, prompt: str) -> Dict[str, Any]:
    """Asynchronous Ray task to make a single request to the LLM API."""
    endpoint = f"{base_url}/chat/completions"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    start_time = time.time()
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(endpoint, json=payload) as response:
                response.raise_for_status()
                response_data = await response.json()

        end_time = time.time()
        latency = end_time - start_time

        response_text = response_data["choices"][0]["message"]["content"]
        input_tokens = len(prompt) // 4
        output_tokens = len(response_text) // 4
        tokens_per_second = output_tokens / latency if latency > 0 else 0

        return {
            "success": True,
            "latency": latency,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "tokens_per_second": tokens_per_second,
            "response_text": response_text,
        }
    except Exception as e:
        end_time = time.time()
        latency = end_time - start_time
        return {
            "success": False,
            "latency": latency,
            "error": str(e),
        }
