import json
from src.mock_test import MockLLMTester
from src.metrics import aggregate_metrics


def test_system_throughput_range():
    config = json.load(open('config/test_config.json'))
    model = config['models'][0]
    tester = MockLLMTester(model)
    test = config['tests'][0]
    results = tester.run_test(test, concurrency=4, total_requests=8)
    summary = aggregate_metrics(results, warmup=0)
    assert 450 <= summary['system_tps'] <= 550
