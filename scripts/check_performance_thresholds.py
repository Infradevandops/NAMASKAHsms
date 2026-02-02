#!/usr/bin/env python3
"""Check performance test results against thresholds."""


import json
import sys
from pathlib import Path

def check_performance_thresholds():

    """Check if performance metrics meet thresholds."""
    stats_file = Path("locust_stats.json")

if not stats_file.exists():
        print("⚠️  No performance stats file found")
        return True  # Don't fail if file doesn't exist

try:
with open(stats_file) as f:
            stats = json.load(f)
except json.JSONDecodeError:
        print("⚠️  Could not parse performance stats")
        return True

    # Define thresholds
    thresholds = {
        "response_time_p95": 500,  # ms
        "response_time_p99": 1000,  # ms
        "error_rate": 0.05,  # 5%
    }

    # Check response times
if "response_times" in stats:
        p95 = stats["response_times"].get("95", 0)
        p99 = stats["response_times"].get("99", 0)

        print("📊 Performance Metrics:")
        print(f"  P95 Response Time: {p95}ms (threshold: {thresholds['response_time_p95']}ms)")
        print(f"  P99 Response Time: {p99}ms (threshold: {thresholds['response_time_p99']}ms)")

if p95 > thresholds["response_time_p95"]:
            print("❌ P95 response time exceeds threshold")
            return False

if p99 > thresholds["response_time_p99"]:
            print("❌ P99 response time exceeds threshold")
            return False

    # Check error rate
if "errors" in stats and "total_requests" in stats:
        error_rate = stats["errors"] / stats["total_requests"]
        print(f"  Error Rate: {error_rate:.2%} (threshold: {thresholds['error_rate']:.2%})")

if error_rate > thresholds["error_rate"]:
            print("❌ Error rate exceeds threshold")
            return False

    print("✅ All performance thresholds met")
    return True


if __name__ == "__main__":
    success = check_performance_thresholds()
    sys.exit(0 if success else 1)