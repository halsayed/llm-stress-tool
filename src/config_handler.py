import json
import os
from typing import Dict, List, Any, Optional


class ConfigHandler:
    """
    Handles loading and validating configuration for LLM stress testing.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the configuration handler.
        
        Args:
            config_path: Path to the configuration JSON file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dict containing the configuration
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def _validate_config(self) -> None:
        """
        Validate the configuration structure and required fields.
        
        Raises:
            ValueError: If configuration is invalid
        """
        required_keys = ['models', 'tests', 'concurrency', 'total_requests']
        
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        # Validate models
        if not isinstance(self.config['models'], list) or len(self.config['models']) == 0:
            raise ValueError("At least one model must be specified")
            
        for model in self.config['models']:
            if not all(k in model for k in ['model_name', 'base_url', 'api_key']):
                raise ValueError("Each model must have model_name, base_url, and api_key")
        
        # Validate tests
        if not isinstance(self.config['tests'], list) or len(self.config['tests']) == 0:
            raise ValueError("At least one test must be specified")
            
        for test in self.config['tests']:
            if not all(k in test for k in ['name', 'input']):
                raise ValueError("Each test must have name and input")
        
        # Validate concurrency
        if not isinstance(self.config['concurrency'], list) or len(self.config['concurrency']) == 0:
            raise ValueError("At least one concurrency level must be specified")
            
        for concurrency in self.config['concurrency']:
            if not isinstance(concurrency, int) or concurrency <= 0:
                raise ValueError("Concurrency levels must be positive integers")
        
        # Validate total_requests
        if not isinstance(self.config['total_requests'], int) or self.config['total_requests'] <= 0:
            raise ValueError("total_requests must be a positive integer")
    
    def get_models(self) -> List[Dict[str, str]]:
        """
        Get the list of models from the configuration.
        
        Returns:
            List of model configurations
        """
        return self.config['models']
    
    def get_tests(self) -> List[Dict[str, Any]]:
        """
        Get the list of tests from the configuration.
        
        Returns:
            List of test configurations
        """
        return self.config['tests']
    
    def get_concurrency_levels(self) -> List[int]:
        """
        Get the list of concurrency levels from the configuration.
        
        Returns:
            List of concurrency levels
        """
        return self.config['concurrency']
    
    def get_total_requests(self) -> int:
        """
        Get the total number of requests to run per test.
        
        Returns:
            Total number of requests
        """
        return self.config['total_requests']
    
    def get_output_config(self) -> Dict[str, Any]:
        """
        Get the output configuration.
        
        Returns:
            Output configuration dictionary
        """
        default_output = {
            "json_output": "results.json",
            "word_report": "llm_performance_report.docx",
            "automated_analysis": False
        }
        
        if 'output' in self.config:
            # Merge with defaults
            return {**default_output, **self.config['output']}
        
        return default_output
