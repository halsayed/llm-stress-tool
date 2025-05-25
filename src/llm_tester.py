import asyncio
import time
from typing import Dict, List, Any

import aiohttp
from tqdm import tqdm


class LLMTester:
    """
    Handles LLM API testing with various prompts and concurrency levels.
    """
    
    def __init__(self, model_config: Dict[str, str]):
        """
        Initialize the LLM tester.
        
        Args:
            model_config: Dictionary containing model configuration
        """
        self.model_name = model_config['model_name']
        self.base_url = model_config['base_url']
        self.api_key = model_config['api_key']
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _count_tokens(self, text: str) -> int:
        """
        Estimate token count for a given text.
        This is a simple approximation - in production, use a proper tokenizer.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        # Simple approximation: ~4 chars per token for English text
        return len(text) // 4
    
    async def _make_request(self, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, prompt: str) -> Dict[str, Any]:
        """Make a single asynchronous request to the LLM API."""
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        async with semaphore:
            start_ts = time.time()
            try:
                async with session.post(endpoint, headers=self.headers, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                end_ts = time.time()
                latency = end_ts - start_ts
                response_text = data["choices"][0]["message"]["content"]
                input_tokens = self._count_tokens(prompt)
                output_tokens = self._count_tokens(response_text)
                tokens_per_second = output_tokens / latency if latency > 0 else 0
                return {
                    "success": True,
                    "latency": latency,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "tokens_per_second": tokens_per_second,
                    "response_text": response_text,
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                }
            except Exception as e:
                end_ts = time.time()
                latency = end_ts - start_ts
                return {
                    "success": False,
                    "latency": latency,
                    "error": str(e),
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                }
    
    def run_test(self, test: Dict[str, Any], concurrency: int, total_requests: int) -> List[Dict[str, Any]]:
        """
        Run a test with specified concurrency and number of requests.
        
        Args:
            test: Test configuration
            concurrency: Number of concurrent requests
            total_requests: Total number of requests to make
            
        Returns:
            List of result dictionaries
        """
        prompt = test['input']
        test_name = test['name']
        
        print(f"Running test '{test_name}' with concurrency {concurrency} on model {self.model_name}")
        
        async def _run() -> List[Dict[str, Any]]:
            semaphore = asyncio.Semaphore(concurrency)
            async with aiohttp.ClientSession() as session:
                tasks = [asyncio.create_task(self._make_request(session, semaphore, prompt)) for _ in range(total_requests)]
                results_local = []
                for coro in tqdm(asyncio.as_completed(tasks), total=total_requests, desc=f"Test: {test_name}"):
                    res = await coro
                    results_local.append(res)
                return results_local

        results = asyncio.run(_run())
        for idx, res in enumerate(results):
            res["test_name"] = test_name
            res["request_id"] = idx
        return results
