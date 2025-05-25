
import sys
from unittest.mock import MagicMock

# Create mock modules
sys.modules['src.llm_tester'] = MagicMock()

# Import the mocks from this file
from src.mock_test import MockLLMTester

# Replace the classes in the mocked modules
sys.modules['src.llm_tester'].LLMTester = MockLLMTester
