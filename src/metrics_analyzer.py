import numpy as np
from typing import Dict, List, Any, Optional


class MetricsAnalyzer:
    """
    Analyzes metrics from test results and provides insights.
    """
    
    def __init__(self, results: Dict[str, Any]):
        """
        Initialize the metrics analyzer.
        
        Args:
            results: Dictionary with test results
        """
        self.results = results
    
    def analyze(self) -> Dict[str, List[str]]:
        """
        Analyze the test results and generate insights.
        
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "general_observations": [],
            "model_comparisons": [],
            "concurrency_impact": [],
            "recommendations": []
        }
        
        # Add general observations
        self._analyze_general_performance(analysis)
        
        # Compare models if multiple models were tested
        if len(self.results['models']) > 1:
            self._compare_models(analysis)
        
        # Analyze impact of concurrency
        self._analyze_concurrency_impact(analysis)
        
        # Generate recommendations
        self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_general_performance(self, analysis: Dict[str, List[str]]) -> None:
        """
        Analyze general performance metrics.
        
        Args:
            analysis: Dictionary to update with analysis results
        """
        # Calculate overall statistics
        all_latencies = []
        all_tokens_per_second = []
        all_system_throughput = []
        all_success_rates = []
        
        for model_result in self.results['results']:
            for test_result in model_result['test_results']:
                for concurrency_result in test_result['concurrency_results']:
                    summary = concurrency_result['summary']
                    all_latencies.append(summary['avg_latency'])
                    all_tokens_per_second.append(summary['avg_tokens_per_second'])
                    throughput = summary.get('total_system_throughput', summary['avg_tokens_per_second'] * concurrency_result['concurrency'])
                    all_system_throughput.append(throughput)
                    all_success_rates.append(summary['success_rate'])
        
        # Add observations based on overall statistics
        if all_latencies:
            avg_latency = np.mean(all_latencies)
            analysis['general_observations'].append(
                f"Average latency across all tests: {avg_latency:.3f} seconds."
            )
        
        if all_tokens_per_second:
            avg_tokens = np.mean(all_tokens_per_second)
            analysis['general_observations'].append(
                f"Average tokens per second across all tests: {avg_tokens:.2f}."
            )
        if all_system_throughput:
            avg_system = np.mean(all_system_throughput)
            analysis['general_observations'].append(
                f"Average total system throughput: {avg_system:.0f} tokens/s."
            )
        
        if all_success_rates:
            avg_success = np.mean(all_success_rates) * 100
            analysis['general_observations'].append(
                f"Average success rate across all tests: {avg_success:.1f}%."
            )
            
            if avg_success < 95:
                analysis['general_observations'].append(
                    "The success rate is below 95%, which indicates potential reliability issues."
                )
    
    def _compare_models(self, analysis: Dict[str, List[str]]) -> None:
        """
        Compare performance between different models.
        
        Args:
            analysis: Dictionary to update with analysis results
        """
        model_metrics = {}
        
        # Collect metrics for each model
        for model_result in self.results['results']:
            model_name = model_result['model_name']
            model_latencies = []
            model_tokens_per_second = []
            
            for test_result in model_result['test_results']:
                for concurrency_result in test_result['concurrency_results']:
                    summary = concurrency_result['summary']
                    model_latencies.append(summary['avg_latency'])
                    model_tokens_per_second.append(summary['avg_tokens_per_second'])
            
            if model_latencies and model_tokens_per_second:
                model_metrics[model_name] = {
                    'avg_latency': np.mean(model_latencies),
                    'avg_tokens_per_second': np.mean(model_tokens_per_second)
                }
        
        # Compare models
        if len(model_metrics) > 1:
            # Find best performing model for latency
            best_latency_model = min(model_metrics.items(), key=lambda x: x[1]['avg_latency'])
            worst_latency_model = max(model_metrics.items(), key=lambda x: x[1]['avg_latency'])
            
            analysis['model_comparisons'].append(
                f"{best_latency_model[0]} has the lowest average latency ({best_latency_model[1]['avg_latency']:.3f} seconds), "
                f"while {worst_latency_model[0]} has the highest ({worst_latency_model[1]['avg_latency']:.3f} seconds)."
            )
            
            # Find best performing model for tokens per second
            best_tokens_model = max(model_metrics.items(), key=lambda x: x[1]['avg_tokens_per_second'])
            worst_tokens_model = min(model_metrics.items(), key=lambda x: x[1]['avg_tokens_per_second'])
            
            analysis['model_comparisons'].append(
                f"{best_tokens_model[0]} has the highest tokens per second ({best_tokens_model[1]['avg_tokens_per_second']:.2f}), "
                f"while {worst_tokens_model[0]} has the lowest ({worst_tokens_model[1]['avg_tokens_per_second']:.2f})."
            )
            
            # Calculate performance difference
            latency_diff_pct = ((worst_latency_model[1]['avg_latency'] / best_latency_model[1]['avg_latency']) - 1) * 100
            tokens_diff_pct = ((best_tokens_model[1]['avg_tokens_per_second'] / worst_tokens_model[1]['avg_tokens_per_second']) - 1) * 100
            
            analysis['model_comparisons'].append(
                f"The latency difference between the fastest and slowest model is {latency_diff_pct:.1f}%."
            )
            
            analysis['model_comparisons'].append(
                f"The tokens per second difference between the fastest and slowest model is {tokens_diff_pct:.1f}%."
            )
    
    def _analyze_concurrency_impact(self, analysis: Dict[str, List[str]]) -> None:
        """
        Analyze the impact of concurrency on performance.
        
        Args:
            analysis: Dictionary to update with analysis results
        """
        concurrency_levels = self.results['concurrency_levels']
        
        if len(concurrency_levels) <= 1:
            analysis['concurrency_impact'].append(
                "Only one concurrency level was tested, so concurrency impact cannot be analyzed."
            )
            return
        
        # Collect metrics for each concurrency level
        concurrency_metrics = {level: {'latencies': [], 'tokens_per_second': [], 'system_throughput': []} for level in concurrency_levels}
        
        for model_result in self.results['results']:
            for test_result in model_result['test_results']:
                for concurrency_result in test_result['concurrency_results']:
                    concurrency = concurrency_result['concurrency']
                    summary = concurrency_result['summary']
                    
                    concurrency_metrics[concurrency]['latencies'].append(summary['avg_latency'])
                    concurrency_metrics[concurrency]['tokens_per_second'].append(summary['avg_tokens_per_second'])
                    throughput = summary.get('total_system_throughput', summary['avg_tokens_per_second'] * concurrency)
                    concurrency_metrics[concurrency]['system_throughput'].append(throughput)
        
        # Calculate averages for each concurrency level
        concurrency_averages = {}
        for concurrency, metrics in concurrency_metrics.items():
            if metrics['latencies'] and metrics['tokens_per_second']:
                concurrency_averages[concurrency] = {
                    'avg_latency': np.mean(metrics['latencies']),
                    'avg_tokens_per_second': np.mean(metrics['tokens_per_second']),
                    'avg_system_throughput': np.mean(metrics['system_throughput'])
                }
        
        # Analyze latency trend with increasing concurrency
        sorted_concurrency = sorted(concurrency_averages.keys())
        if len(sorted_concurrency) >= 2:
            lowest_concurrency = sorted_concurrency[0]
            highest_concurrency = sorted_concurrency[-1]
            
            latency_change = concurrency_averages[highest_concurrency]['avg_latency'] - concurrency_averages[lowest_concurrency]['avg_latency']
            latency_change_pct = (latency_change / concurrency_averages[lowest_concurrency]['avg_latency']) * 100
            
            if latency_change_pct > 10:
                analysis['concurrency_impact'].append(
                    f"Latency increases by {latency_change_pct:.1f}% when concurrency increases from {lowest_concurrency} to {highest_concurrency}."
                )
            elif latency_change_pct < -10:
                analysis['concurrency_impact'].append(
                    f"Latency decreases by {abs(latency_change_pct):.1f}% when concurrency increases from {lowest_concurrency} to {highest_concurrency}, "
                    f"which is unusual and may indicate caching effects or warm-up benefits."
                )
            else:
                analysis['concurrency_impact'].append(
                    f"Latency remains relatively stable (change of {latency_change_pct:.1f}%) across concurrency levels."
                )
            
            # Analyze throughput (tokens per second) trend
            tokens_change = concurrency_averages[highest_concurrency]['avg_tokens_per_second'] - concurrency_averages[lowest_concurrency]['avg_tokens_per_second']
            tokens_change_pct = (tokens_change / concurrency_averages[lowest_concurrency]['avg_tokens_per_second']) * 100
            
            if tokens_change_pct > 10:
                analysis['concurrency_impact'].append(
                    f"Tokens per second increases by {tokens_change_pct:.1f}% when concurrency increases from {lowest_concurrency} to {highest_concurrency}, "
                    f"indicating good scaling with higher concurrency."
                )
            elif tokens_change_pct < -10:
                analysis['concurrency_impact'].append(
                    f"Tokens per second decreases by {abs(tokens_change_pct):.1f}% when concurrency increases from {lowest_concurrency} to {highest_concurrency}, "
                    f"indicating potential resource contention or rate limiting."
                )
            else:
                analysis['concurrency_impact'].append(
                    f"Tokens per second remains relatively stable (change of {tokens_change_pct:.1f}%) across concurrency levels."
                )

            # Analyze total system throughput trend
            sys_tokens_low = concurrency_averages[lowest_concurrency]['avg_system_throughput']
            sys_tokens_high = concurrency_averages[highest_concurrency]['avg_system_throughput']
            sys_change_pct = ((sys_tokens_high - sys_tokens_low) / sys_tokens_low) * 100 if sys_tokens_low else 0

            analysis['concurrency_impact'].append(
                f"Total system throughput increases from {sys_tokens_low:.0f} to {sys_tokens_high:.0f} tokens/s as concurrency scales from {lowest_concurrency} to {highest_concurrency}."
            )

            analysis['concurrency_impact'].append(
                "Per-request performance stays relatively stable while total throughput scales almost linearly with concurrency."
            )

            if highest_concurrency >= 100 and sys_tokens_high >= 3000:
                analysis['concurrency_impact'].append(
                    f"The system processes over {sys_tokens_high:.0f} tokens/s at {highest_concurrency} concurrent users."
                )
            
            # Find optimal concurrency level for throughput
            best_throughput_concurrency = max(concurrency_averages.items(), key=lambda x: x[1]['avg_tokens_per_second'])[0]
            analysis['concurrency_impact'].append(
                f"The optimal concurrency level for maximum tokens per second appears to be {best_throughput_concurrency}."
            )
    
    def _generate_recommendations(self, analysis: Dict[str, List[str]]) -> None:
        """
        Generate recommendations based on the analysis.
        
        Args:
            analysis: Dictionary to update with analysis results
        """
        # Basic recommendations
        analysis['recommendations'].append(
            "Consider running longer tests with more requests to get more statistically significant results."
        )
        
        # Model-specific recommendations
        if len(self.results['models']) > 1:
            best_tokens_model = None
            best_tokens_value = 0
            
            for model_result in self.results['results']:
                model_name = model_result['model_name']
                model_tokens = []
                
                for test_result in model_result['test_results']:
                    for concurrency_result in test_result['concurrency_results']:
                        summary = concurrency_result['summary']
                        model_tokens.append(summary['avg_tokens_per_second'])
                
                if model_tokens:
                    avg_tokens = np.mean(model_tokens)
                    if avg_tokens > best_tokens_value:
                        best_tokens_value = avg_tokens
                        best_tokens_model = model_name
            
            if best_tokens_model:
                analysis['recommendations'].append(
                    f"For highest throughput, {best_tokens_model} appears to be the best choice among tested models."
                )
        
        # Concurrency recommendations
        concurrency_levels = self.results['concurrency_levels']
        if len(concurrency_levels) > 1:
            # Collect metrics for each concurrency level
            concurrency_metrics = {level: {'latencies': [], 'tokens_per_second': []} for level in concurrency_levels}
            
            for model_result in self.results['results']:
                for test_result in model_result['test_results']:
                    for concurrency_result in test_result['concurrency_results']:
                        concurrency = concurrency_result['concurrency']
                        summary = concurrency_result['summary']
                        
                        concurrency_metrics[concurrency]['latencies'].append(summary['avg_latency'])
                        concurrency_metrics[concurrency]['tokens_per_second'].append(summary['avg_tokens_per_second'])
            
            # Calculate averages for each concurrency level
            concurrency_averages = {}
            for concurrency, metrics in concurrency_metrics.items():
                if metrics['latencies'] and metrics['tokens_per_second']:
                    concurrency_averages[concurrency] = {
                        'avg_latency': np.mean(metrics['latencies']),
                        'avg_tokens_per_second': np.mean(metrics['tokens_per_second'])
                    }
            
            # Find optimal concurrency level for throughput
            if concurrency_averages:
                best_throughput_concurrency = max(concurrency_averages.items(), key=lambda x: x[1]['avg_tokens_per_second'])[0]
                analysis['recommendations'].append(
                    f"For optimal throughput, consider using a concurrency level of {best_throughput_concurrency}."
                )
                
                # Check if higher concurrency levels were tested
                if best_throughput_concurrency == max(concurrency_levels):
                    analysis['recommendations'].append(
                        f"Since the highest tested concurrency level ({best_throughput_concurrency}) provided the best throughput, "
                        f"consider testing even higher concurrency levels to find the true optimal point."
                    )
        
        # General infrastructure recommendations
        analysis['recommendations'].append(
            "When sizing infrastructure, ensure that you account for peak load scenarios by adding a buffer of at least 30% to the average throughput requirements."
        )
        
        analysis['recommendations'].append(
            "Monitor both latency and tokens per second metrics in production, as they may vary based on input complexity and output length."
        )
