#!/usr/bin/env python3
"""
Performance Threshold Checker
Validates that performance metrics meet requirements.
"""
import json
import sys
from pathlib import Path


def check_thresholds():
    """Check performance thresholds from Locust results."""
    
    # Look for Locust stats file
    stats_file = Path("locust_stats.json")
    
    if not stats_file.exists():
        print("⚠️  No performance stats found, skipping check")
        return 0
    
    with open(stats_file) as f:
        stats = json.load(f)
    
    # Define thresholds
    MAX_P95_MS = 500
    MAX_ERROR_RATE = 0.05  # 5%
    
    failures = []
    
    for endpoint in stats.get("stats", []):
        name = endpoint.get("name")
        p95 = endpoint.get("response_time_percentile_95", 0)
        error_rate = endpoint.get("failure_rate", 0)
        
        if p95 > MAX_P95_MS:
            failures.append(f"❌ {name}: p95={p95}ms (max: {MAX_P95_MS}ms)")
        
        if error_rate > MAX_ERROR_RATE:
            failures.append(f"❌ {name}: error_rate={error_rate*100:.1f}% (max: {MAX_ERROR_RATE*100}%)")
    
    if failures:
        print("❌ Performance thresholds exceeded:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    
    print("✅ All performance thresholds met")
    return 0


if __name__ == "__main__":
    sys.exit(check_thresholds())
