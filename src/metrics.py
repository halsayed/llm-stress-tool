import numpy as np
from typing import List, Dict, Any

def aggregate_metrics(results: List[Dict[str, Any]], warmup: int = 0) -> Dict[str, Any]:
    """Aggregate request metrics with optional warmup period."""
    if warmup < 0:
        warmup = 0
    filtered = [r for r in results[warmup:] if r.get("success", False)]
    total_requests = len(results)
    successful_requests = len(filtered)
    if not filtered:
        return {
            "success_rate": 0.0,
            "lat_avg": 0.0,
            "lat_p50": 0.0,
            "lat_p95": 0.0,
            "lat_p99": 0.0,
            "avg_tokens_per_second": 0.0,
            "system_tps": 0.0,
            "total_requests": total_requests,
            "successful_requests": 0,
        }

    latencies = [r["latency"] for r in filtered]
    lat_avg = float(np.mean(latencies))
    lat_p50 = float(np.percentile(latencies, 50))
    lat_p95 = float(np.percentile(latencies, 95))
    lat_p99 = float(np.percentile(latencies, 99))

    tps_values = [r.get("output_tokens", 0) / r["latency"] if r["latency"] else 0 for r in filtered]
    avg_tps = float(np.mean(tps_values)) if tps_values else 0.0

    start_times = [r.get("start_ts", 0) for r in filtered]
    end_times = [r.get("end_ts", r.get("start_ts", 0)) for r in filtered]
    total_tokens = sum(r.get("output_tokens", 0) for r in filtered)
    wall_clock = max(end_times) - min(start_times) if start_times and end_times else 0
    system_tps = total_tokens / wall_clock if wall_clock > 0 else 0.0

    return {
        "success_rate": successful_requests / total_requests,
        "lat_avg": lat_avg,
        "lat_p50": lat_p50,
        "lat_p95": lat_p95,
        "lat_p99": lat_p99,
        "avg_tokens_per_second": avg_tps,
        "system_tps": system_tps,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
    }
