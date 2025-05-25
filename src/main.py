#!/usr/bin/env python3

import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional

# Add the parent directory to the path to make imports work regardless of where the script is run from
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Local imports
try:
    # Try direct imports first (when installed as a package)
    from config_handler import ConfigHandler
    from llm_tester import LLMTester
    from report_generator import ReportGenerator
    from metrics_analyzer import MetricsAnalyzer
    from metrics import aggregate_metrics
except ImportError:
    # Fall back to fully qualified imports (when run directly)
    from src.config_handler import ConfigHandler
    from src.llm_tester import LLMTester
    from src.report_generator import ReportGenerator
    from src.metrics_analyzer import MetricsAnalyzer
    from src.metrics import aggregate_metrics


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='LLM Stress Testing Tool')
    parser.add_argument('--config', type=str, required=True, 
                        help='Path to configuration JSON file')
    parser.add_argument('--output-dir', type=str, default='./results',
                        help='Directory to store results (default: ./results)')
    parser.add_argument('--no-report', action='store_true',
                        help='Skip generating Word report')
    parser.add_argument('--no-analysis', action='store_true',
                        help='Skip automated analysis')
    parser.add_argument('--warmup', type=int, default=3,
                        help='Number of warmup iterations to skip in metrics')
    
    return parser.parse_args()


def ensure_output_directory(output_dir: str) -> None:
    """Ensure the output directory exists."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")


def run_tests(config_handler: ConfigHandler, output_dir: str, warmup: int) -> Dict[str, Any]:
    """
    Run all tests according to configuration.
    
    Args:
        config_handler: Configuration handler instance
        output_dir: Directory to store results
        
    Returns:
        Dictionary with all test results
    """
    models = config_handler.get_models()
    tests = config_handler.get_tests()
    concurrency_levels = config_handler.get_concurrency_levels()
    total_requests = config_handler.get_total_requests()
    
    all_results = {
        "models": [],
        "tests": [],
        "concurrency_levels": concurrency_levels,
        "total_requests": total_requests,
        "results": []
    }
    
    # Store model and test information
    all_results["models"] = [{"model_name": model["model_name"], "base_url": model["base_url"]} 
                            for model in models]
    all_results["tests"] = tests
    
    # Run tests for each model
    for model_config in models:
        model_name = model_config["model_name"]
        print(f"\n=== Testing model: {model_name} ===")
        
        # Initialize tester
        tester = LLMTester(model_config)
        
        model_results = {
            "model_name": model_name,
            "test_results": []
        }
        
        # Run each test with different concurrency levels
        for test in tests:
            test_name = test["name"]
            print(f"\n--- Test: {test_name} ---")
            
            test_results = {
                "test_name": test_name,
                "concurrency_results": []
            }
            
            for concurrency in concurrency_levels:
                print(f"\nConcurrency level: {concurrency}")
                
                # Run test once with LLMTester
                results = tester.run_test(test, concurrency, total_requests)

                concurrency_result = {
                    "concurrency": concurrency,
                    "request_results": results,
                    "summary": calculate_summary(results, warmup, concurrency)
                }
                
                test_results["concurrency_results"].append(concurrency_result)
            
            model_results["test_results"].append(test_results)
        
        all_results["results"].append(model_results)
    
    # Save results to JSON file
    output_config = config_handler.get_output_config()
    json_output_path = os.path.join(output_dir, output_config["json_output"])
    
    with open(json_output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nResults saved to {json_output_path}")
    
    return all_results


def calculate_summary(results: List[Dict[str, Any]], warmup: int, concurrency: int) -> Dict[str, Any]:
    """Calculate summary statistics using aggregate_metrics."""
    summary = aggregate_metrics(results, warmup)
    summary["concurrency"] = concurrency
    return summary


def main():
    """Main entry point for the LLM stress testing tool."""
    args = parse_arguments()
    
    try:
        # Ensure output directory exists
        ensure_output_directory(args.output_dir)
        
        # Load and validate configuration
        print(f"Loading configuration from {args.config}")
        config_handler = ConfigHandler(args.config)
        
        # Run tests
        all_results = run_tests(config_handler, args.output_dir, args.warmup)
        
        # Generate report if not disabled
        if not args.no_report:
            output_config = config_handler.get_output_config()
            word_report_path = os.path.join(args.output_dir, output_config["word_report"])
            
            print(f"\nGenerating Word report: {word_report_path}")
            report_generator = ReportGenerator(all_results, word_report_path)
            report_generator.generate_report()
            
            # Run automated analysis if enabled
            if output_config.get("automated_analysis", False) and not args.no_analysis:
                print("\nRunning automated analysis")
                analyzer = MetricsAnalyzer(all_results)
                analysis = analyzer.analyze()
                report_generator.add_analysis(analysis)
            
            print(f"Report generated: {word_report_path}")
        
        print("\nLLM stress testing completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
