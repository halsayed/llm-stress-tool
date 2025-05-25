#!/usr/bin/env python3

import os
import sys
import json
import argparse
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import mock modules
from src.mock_test import MockLLMTester
from src.config_handler import ConfigHandler
from src.report_generator import ReportGenerator
from src.metrics_analyzer import MetricsAnalyzer
from src.metrics import aggregate_metrics


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='LLM Stress Testing Tool - Test Runner')
    parser.add_argument('--config', type=str, default='./config/test_config.json',
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


def ensure_output_directory(output_dir):
    """Ensure the output directory exists."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")


def calculate_summary(results, warmup, concurrency):
    """Calculate summary statistics using aggregate_metrics."""
    summary = aggregate_metrics(results, warmup)
    summary["concurrency"] = concurrency
    return summary


def run_tests(config_handler, output_dir, warmup):
    """Run all tests according to configuration."""
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
        
        # Initialize mock testers
        tester = MockLLMTester(model_config)
        
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
                
                # Run test once with MockLLMTester
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
    
    return all_results, json_output_path


def main():
    """Main entry point for the test runner."""
    args = parse_arguments()
    
    try:
        # Ensure output directory exists
        ensure_output_directory(args.output_dir)
        
        # Load and validate configuration
        print(f"Loading configuration from {args.config}")
        config_handler = ConfigHandler(args.config)
        
        # Run tests
        all_results, json_output_path = run_tests(config_handler, args.output_dir, args.warmup)
        
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
        print(f"Results available at: {json_output_path}")
        
        return 0, json_output_path
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1, None


if __name__ == "__main__":
    exit_code, _ = main()
    sys.exit(exit_code)
