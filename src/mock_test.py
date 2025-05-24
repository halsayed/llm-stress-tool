import os
import sys
import json
from typing import Dict, Any

# Mock implementation for testing without actual API calls
class MockLLMTester:
    """
    Mock implementation of LLMTester for testing without actual API calls.
    """
    
    def __init__(self, model_config: Dict[str, str]):
        """
        Initialize the mock LLM tester.
        
        Args:
            model_config: Dictionary containing model configuration
        """
        self.model_name = model_config['model_name']
        self.base_url = model_config['base_url']
        self.api_key = model_config['api_key']
    
    def run_test(self, test: Dict[str, Any], concurrency: int, total_requests: int) -> list:
        """
        Run a mock test with specified concurrency and number of requests.
        
        Args:
            test: Test configuration
            concurrency: Number of concurrent requests
            total_requests: Total number of requests to make
            
        Returns:
            List of result dictionaries
        """
        print(f"[MOCK] Running test '{test['name']}' with concurrency {concurrency} on model {self.model_name}")
        
        results = []
        
        # Generate mock results
        for i in range(total_requests):
            # Simulate varying latency based on concurrency
            base_latency = 0.5 + (len(test['input']) / 1000)  # Base latency depends on input length
            concurrency_factor = 1.0 + (concurrency * 0.1)  # Higher concurrency increases latency
            latency = base_latency * concurrency_factor
            
            # Simulate varying token counts
            input_tokens = len(test['input']) // 4
            output_tokens = test.get('expected_output_tokens', 100)
            
            # Simulate tokens per second
            tokens_per_second = output_tokens / latency
            
            # Create result
            result = {
                "success": True,
                "latency": latency,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "tokens_per_second": tokens_per_second,
                "test_name": test['name'],
                "request_id": i,
                "response_text": f"Mock response for test {test['name']}, request {i}"
            }
            
            results.append(result)
        
        return results


class MockLLMPerfRunner:
    """
    Mock implementation of LLMPerfRunner for testing without actual API calls.
    """
    
    def __init__(self, model_config: Dict[str, str]):
        """
        Initialize the mock LLMPerf runner.
        
        Args:
            model_config: Dictionary containing model configuration
        """
        self.model_name = model_config['model_name']
        self.base_url = model_config['base_url']
        self.api_key = model_config['api_key']
    
    def run_benchmark(self, prompt: str, concurrency: int, total_requests: int) -> Dict[str, Any]:
        """
        Run a mock benchmark.
        
        Args:
            prompt: Input prompt text
            concurrency: Number of concurrent requests
            total_requests: Total number of requests to make
            
        Returns:
            Dictionary with benchmark results
        """
        print(f"[MOCK] Running LLMPerf benchmark with concurrency {concurrency} on model {self.model_name}")
        
        # Generate mock benchmark results
        base_latency = 0.5 + (len(prompt) / 1000)
        concurrency_factor = 1.0 + (concurrency * 0.1)
        avg_latency = base_latency * concurrency_factor
        
        # Calculate mock percentiles
        p50_latency = avg_latency * 0.9
        p90_latency = avg_latency * 1.5
        p99_latency = avg_latency * 2.0
        
        # Calculate mock throughput
        throughput = concurrency / avg_latency
        
        # Calculate mock tokens per second
        output_tokens = 100  # Assume average output tokens
        tokens_per_second = (output_tokens * total_requests) / (avg_latency * total_requests / concurrency)
        
        return {
            "success": True,
            "throughput": throughput,
            "avg_latency": avg_latency,
            "p50_latency": p50_latency,
            "p90_latency": p90_latency,
            "p99_latency": p99_latency,
            "tokens_per_second": tokens_per_second,
            "total_tokens": output_tokens * total_requests,
            "successful_requests": total_requests,
            "failed_requests": 0
        }


# Mock the imports in main.py
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create mock modules
with open('/home/ubuntu/llm_stress_tool/src/mock_imports.py', 'w') as f:
    f.write("""
import sys
from unittest.mock import MagicMock

# Create mock modules
sys.modules['src.llm_tester'] = MagicMock()
sys.modules['src.llmperf_integration'] = MagicMock()

# Import the mocks from this file
from src.mock_test import MockLLMTester, MockLLMPerfRunner

# Replace the classes in the mocked modules
sys.modules['src.llm_tester'].LLMTester = MockLLMTester
sys.modules['src.llmperf_integration'].LLMPerfRunner = MockLLMPerfRunner
""")

if __name__ == "__main__":
    print("Mock test implementation created for testing without API keys.")
