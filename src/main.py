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
except ImportError:
    # Fall back to fully qualified imports (when run directly)
    from src.config_handler import ConfigHandler
    from src.llm_tester import LLMTester
    from src.report_generator import ReportGenerator
    from src.metrics_analyzer import MetricsAnalyzer


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
    
    return parser.parse_args()


def ensure_output_directory(output_dir: str) -> None:
    """Ensure the output directory exists."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")


def run_tests(config_handler: ConfigHandler, output_dir: str) -> Dict[str, Any]:
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
                
                # Combine results
                concurrency_result = {
                    "concurrency": concurrency,
                    "request_results": results,
                    "summary": calculate_summary(results)
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


def calculate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from test results.
    
    Args:
        results: List of test result dictionaries
        
    Returns:
        Dictionary with summary statistics
    """
    successful_results = [r for r in results if r.get("success", False)]
    
    if not successful_results:
        return {
            "success_rate": 0,
            "avg_latency": 0,
            "avg_tokens_per_second": 0,
            "total_requests": len(results),
            "successful_requests": 0
        }
    
    total_requests = len(results)
    successful_requests = len(successful_results)
    
    avg_latency = sum(r["latency"] for r in successful_results) / successful_requests
    avg_tokens_per_second = sum(r.get("tokens_per_second", 0) for r in successful_results) / successful_requests

    # Calculate latency percentiles and throughput
    latencies = sorted(r["latency"] for r in successful_results)
    p50_index = int(len(latencies) * 0.5)
    p90_index = int(len(latencies) * 0.9)
    p99_index = int(len(latencies) * 0.99)

    p50_latency = latencies[p50_index] if latencies else 0
    p90_latency = latencies[p90_index] if latencies else 0
    p99_latency = latencies[p99_index] if latencies else 0

    total_latency = sum(latencies)
    throughput = successful_requests / total_latency if total_latency > 0 else 0

    return {
        "success_rate": successful_requests / total_requests,
        "avg_latency": avg_latency,
        "avg_tokens_per_second": avg_tokens_per_second,
        "p50_latency": p50_latency,
        "p90_latency": p90_latency,
        "p99_latency": p99_latency,
        "throughput": throughput,
        "total_requests": total_requests,
        "successful_requests": successful_requests
    }


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
        all_results = run_tests(config_handler, args.output_dir)
        
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
