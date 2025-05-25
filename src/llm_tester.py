import json
import time
from typing import Dict, List, Any
import requests
from tqdm import tqdm
import ray
try:
    from .ray_requests import make_request
except ImportError:  # Allow running without package context
    from src.ray_requests import make_request


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
    
    def _make_request(self, prompt: str) -> Dict[str, Any]:
        """
        Make a single request to the LLM API.
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Dictionary with response data and metrics
        """
        endpoint = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            end_time = time.time()
            latency = end_time - start_time
            
            # Extract response text
            response_text = response_data['choices'][0]['message']['content']
            
            # Calculate tokens
            input_tokens = self._count_tokens(prompt)
            output_tokens = self._count_tokens(response_text)
            
            # Calculate tokens per second
            tokens_per_second = output_tokens / latency if latency > 0 else 0
            
            return {
                "success": True,
                "latency": latency,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "tokens_per_second": tokens_per_second,
                "response_text": response_text
            }
            
        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            
            return {
                "success": False,
                "latency": latency,
                "error": str(e)
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
        
        results = []
        
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

        with tqdm(total=total_requests, desc=f"Test: {test_name}") as pbar:
            pending = []
            for request_id in range(total_requests):
                pending.append((request_id, make_request.remote(self.base_url, self.headers, self.model_name, prompt)))

                if len(pending) == concurrency or request_id == total_requests - 1:
                    ids, refs = zip(*pending)
                    batch_results = ray.get(list(refs))
                    for rid, res in zip(ids, batch_results):
                        res["test_name"] = test_name
                        res["request_id"] = rid
                    results.extend(batch_results)
                    pbar.update(len(batch_results))
                    pending = []

        return results
