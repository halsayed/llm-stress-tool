import json
import os
from typing import Dict, List, Any
import requests
import time
from tqdm import tqdm
import ray
from .ray_requests import make_request

# Remove the dependency on llmperf.benchmark
class LLMPerfRunner:
    """
    Custom implementation of LLM benchmarking without llmperf dependency.
    """
    
    def __init__(self, model_config: Dict[str, str]):
        """
        Initialize the LLM benchmark runner.
        
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
    
    def run_benchmark(self, prompt: str, concurrency: int, total_requests: int) -> Dict[str, Any]:
        """
        Run a benchmark with specified concurrency and number of requests.
        
        Args:
            prompt: Input prompt text
            concurrency: Number of concurrent requests
            total_requests: Total number of requests to make
            
        Returns:
            Dictionary with benchmark results
        """
        print(f"Running benchmark with concurrency {concurrency} on model {self.model_name}")
        
        results = []
        latencies = []
        tokens_per_second_values = []
        total_tokens = 0
        successful_requests = 0
        failed_requests = 0

        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

        with tqdm(total=total_requests, desc=f"Benchmark") as pbar:
            pending = []
            for _ in range(total_requests):
                pending.append(make_request.remote(self.base_url, self.headers, self.model_name, prompt))

                if len(pending) == concurrency or len(results) + len(pending) == total_requests:
                    batch_results = ray.get(pending)
                    pending = []
                    for result in batch_results:
                        if result.get("success", False):
                            latencies.append(result["latency"])
                            tokens_per_second_values.append(result.get("tokens_per_second", 0))
                            total_tokens += result.get("output_tokens", 0)
                            successful_requests += 1
                        else:
                            failed_requests += 1

                    results.extend(batch_results)
                    pbar.update(len(batch_results))
        
        # Calculate metrics
        if successful_requests > 0:
            avg_latency = sum(latencies) / successful_requests
            tokens_per_second = sum(tokens_per_second_values) / successful_requests
            
            # Calculate percentiles
            latencies.sort()
            p50_index = int(len(latencies) * 0.5)
            p90_index = int(len(latencies) * 0.9)
            p99_index = int(len(latencies) * 0.99)
            
            p50_latency = latencies[p50_index] if p50_index < len(latencies) else latencies[-1]
            p90_latency = latencies[p90_index] if p90_index < len(latencies) else latencies[-1]
            p99_latency = latencies[p99_index] if p99_index < len(latencies) else latencies[-1]
            
            # Calculate throughput
            throughput = successful_requests / sum(latencies) if sum(latencies) > 0 else 0
        else:
            avg_latency = 0
            tokens_per_second = 0
            p50_latency = 0
            p90_latency = 0
            p99_latency = 0
            throughput = 0
        
        return {
            "success": successful_requests > 0,
            "throughput": throughput,
            "avg_latency": avg_latency,
            "p50_latency": p50_latency,
            "p90_latency": p90_latency,
            "p99_latency": p99_latency,
            "tokens_per_second": tokens_per_second,
            "total_tokens": total_tokens,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests
        }
