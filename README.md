# LLM Stress Testing Tool - User Guide

## Overview

This tool allows you to benchmark the performance of LLM endpoints using the OpenAI API format. It measures key metrics such as tokens/second, total system throughput, and latency under various load conditions.
Concurrent requests are executed using Ray tasks running on your local machine, so you don't need a separate Ray cluster.

## Features

- Test multiple LLM models with different parameters (model_name, base_url, api_key)
- Define custom input and output tests
- Configure concurrent request levels executed via Ray tasks
- Generate detailed performance reports with visualizations
- Export results to JSON and Word formats
- Optional automated analysis of performance metrics

## Requirements

- Python 3.8+
- Required packages: ray, llmperf, matplotlib, pandas, python-docx, tqdm, requests, aiohttp

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-stress-tool.git
cd llm-stress-tool

# Install dependencies
pip install ray llmperf matplotlib pandas python-docx tqdm requests aiohttp
```

## Configuration

Create a JSON configuration file with the following structure:

```json
{
  "models": [
    {
      "model_name": "gpt-3.5-turbo",
      "base_url": "https://api.openai.com/v1",
      "api_key": "your-api-key-here"
    }
  ],
  "tests": [
    {
      "name": "short_prompt",
      "input": "Explain the concept of machine learning in one paragraph.",
      "expected_output_tokens": 100
    },
    {
      "name": "medium_prompt",
      "input": "Write a short essay about the impact of artificial intelligence on society.",
      "expected_output_tokens": 300
    }
  ],
  "concurrency": [1, 5, 10],
  "total_requests": 50,
  "output": {
    "json_output": "results.json",
    "word_report": "llm_performance_report.docx",
    "automated_analysis": true
  }
}
```

You can also set the environment variable `OPENAI_API_KEY` to override the
`api_key` values in the configuration file. This allows sharing configuration
files without including secrets.

## Usage

```bash
# Run with a specific configuration file
python src/main.py --config path/to/your/config.json

# Specify output directory
python src/main.py --config path/to/your/config.json --output-dir ./my_results

# Skip Word report generation
python src/main.py --config path/to/your/config.json --no-report

# Skip automated analysis
python src/main.py --config path/to/your/config.json --no-analysis
```

## Output

The tool generates:

1. A JSON file with detailed test results
2. A Word document report with:
   - Test configuration details
   - Performance metrics tables
   - Visualizations of latency, tokens/second, and total system throughput
   - Optional automated analysis

## Interpreting Results

- **Tokens/second**: Higher is better, indicates throughput capacity
- **Total system throughput**: Tokens/second multiplied by concurrency. Example: `100 concurrency * 31.83 tokens/s ≈ 3,183 tokens/s`
- **Latency**: Lower is better, indicates response time
- **Success rate**: Higher is better, indicates reliability
- **Concurrency impact**: Shows how performance scales with concurrent requests

## Infrastructure Sizing

Use the results to size your infrastructure:
- Consider peak load scenarios by adding a 30% buffer to average throughput
- Monitor both latency and tokens/second in production
- Select the optimal concurrency level based on the "Concurrency Impact" section

## Troubleshooting

- If you encounter API rate limits, reduce concurrency or total_requests
- For authentication errors, verify your API keys
- For visualization issues, ensure matplotlib is properly installed

## License

This project is licensed under the MIT License - see the LICENSE file for details.
