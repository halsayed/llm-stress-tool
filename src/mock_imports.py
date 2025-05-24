
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
