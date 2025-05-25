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

        # Generate mock results with synthetic timing to emulate concurrency
        for i in range(total_requests):
            base_latency = 0.5 + (len(test['input']) / 1000)
            concurrency_factor = 1.0 + (concurrency * 0.1)
            latency = base_latency * concurrency_factor

            start_ts = (i // concurrency) * latency
            end_ts = start_ts + latency

            input_tokens = len(test['input']) // 4
            output_tokens = test.get('expected_output_tokens', 100)
            tokens_per_second = output_tokens / latency

            result = {
                "success": True,
                "latency": latency,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "tokens_per_second": tokens_per_second,
                "test_name": test['name'],
                "request_id": i,
                "response_text": f"Mock response for test {test['name']}, request {i}",
                "start_ts": start_ts,
                "end_ts": end_ts,
            }

            results.append(result)
        
        return results




# Mock the imports in main.py
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create mock modules
mock_imports_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_imports.py")
with open(mock_imports_path, 'w') as f:
    f.write("""
import sys
from unittest.mock import MagicMock

# Create mock modules
sys.modules['src.llm_tester'] = MagicMock()

# Import the mocks from this file
from src.mock_test import MockLLMTester

# Replace the classes in the mocked modules
sys.modules['src.llm_tester'].LLMTester = MockLLMTester
""")

if __name__ == "__main__":
    print("Mock test implementation created for testing without API keys.")
