#!/usr/bin/env python3
"""Canary deployment strategy for production rollout."""

import os
import sys
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CanaryDeployment:
    """Manage canary deployment with traffic shifting and monitoring."""

    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.canary_percentage = int(os.getenv("CANARY_PERCENTAGE", "10"))
        self.monitoring_interval = 30  # seconds
        self.monitoring_duration = 300  # 5 minutes per stage
        self.error_threshold = 1.0  # 1% error rate
        self.latency_threshold = 500  # 500ms
        self.stages = [10, 25, 50, 100]  # Traffic percentages
        self.current_stage = 0
        self.metrics_history = []

    def get_current_metrics(self) -> Optional[Dict]:
        """Fetch current deployment metrics."""
        try:
            response = requests.get(
                f"{self.api_url}/api/metrics/deployment", timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch metrics: {e}")
        return None

    def check_health(self) -> bool:
        """Check if deployment is healthy."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def evaluate_metrics(self, metrics: Dict) -> Tuple[bool, str]:
        """Evaluate if metrics are within acceptable thresholds."""
        if not metrics:
            return False, "No metrics available"

        error_rate = metrics.get("error_rate", 0)
        p95_latency = metrics.get("p95_latency", 0)
        success_rate = metrics.get("success_rate", 100)

        # Check error rate
        if error_rate > self.error_threshold:
            return False, f"Error rate too high: {error_rate:.2f}%"

        # Check latency
        if p95_latency > self.latency_threshold:
            return False, f"P95 latency too high: {p95_latency:.2f}ms"

        # Check success rate
        if success_rate < 99.0:
            return False, f"Success rate too low: {success_rate:.2f}%"

        return True, "Metrics within acceptable thresholds"

    def shift_traffic(self, percentage: int) -> bool:
        """Shift traffic to new deployment."""
        logger.info(f"Shifting traffic to {percentage}%...")
        try:
            response = requests.post(
                f"{self.api_url}/api/deployment/traffic-shift",
                json={"percentage": percentage},
                timeout=10,
            )
            if response.status_code == 200:
                logger.info(f"✓ Traffic shifted to {percentage}%")
                return True
            else:
                logger.error(f"Traffic shift failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Traffic shift error: {e}")
            return False

    def monitor_stage(self, duration: int) -> Tuple[bool, Dict]:
        """Monitor deployment for specified duration."""
        logger.info(f"Monitoring deployment for {duration} seconds...")

        start_time = time.time()
        stage_metrics = []

        while time.time() - start_time < duration:
            metrics = self.get_current_metrics()
            if metrics:
                stage_metrics.append(metrics)
                healthy, message = self.evaluate_metrics(metrics)

                if not healthy:
                    logger.error(f"Health check failed: {message}")
                    return False, metrics

                logger.info(f"✓ Metrics healthy: {message}")

            time.sleep(self.monitoring_interval)

        # Calculate average metrics
        if stage_metrics:
            avg_metrics = self._calculate_average_metrics(stage_metrics)
            return True, avg_metrics

        return True, {}

    def _calculate_average_metrics(self, metrics_list: List[Dict]) -> Dict:
        """Calculate average metrics from list."""
        if not metrics_list:
            return {}

        avg_metrics = {
            "error_rate": sum(m.get("error_rate", 0) for m in metrics_list)
            / len(metrics_list),
            "p95_latency": sum(m.get("p95_latency", 0) for m in metrics_list)
            / len(metrics_list),
            "success_rate": sum(m.get("success_rate", 100) for m in metrics_list)
            / len(metrics_list),
            "request_count": sum(m.get("request_count", 0) for m in metrics_list),
        }
        return avg_metrics

    def rollback(self) -> bool:
        """Rollback to previous deployment."""
        logger.error("Rolling back deployment...")
        try:
            response = requests.post(
                f"{self.api_url}/api/deployment/rollback", timeout=10
            )
            if response.status_code == 200:
                logger.info("✓ Rollback successful")
                return True
            else:
                logger.error(f"Rollback failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False

    def run_canary_deployment(self) -> bool:
        """Execute canary deployment with traffic shifting."""
        logger.info("Starting canary deployment...")
        logger.info(f"Stages: {self.stages}")

        deployment_report = {
            "timestamp": datetime.now().isoformat(),
            "stages": [],
            "success": False,
        }

        for stage_idx, percentage in enumerate(self.stages):
            logger.info(f"\n{'='*60}")
            logger.info(f"STAGE {stage_idx + 1}: {percentage}% Traffic")
            logger.info(f"{'='*60}")

            # Shift traffic
            if not self.shift_traffic(percentage):
                logger.error(f"Failed to shift traffic to {percentage}%")
                self.rollback()
                return False

            # Monitor stage
            healthy, metrics = self.monitor_stage(self.monitoring_duration)

            stage_report = {
                "stage": stage_idx + 1,
                "percentage": percentage,
                "duration": self.monitoring_duration,
                "healthy": healthy,
                "metrics": metrics,
            }
            deployment_report["stages"].append(stage_report)

            if not healthy:
                logger.error(f"Stage {stage_idx + 1} failed health checks")
                self.rollback()
                return False

            logger.info(f"✓ Stage {stage_idx + 1} passed")

            # Wait before next stage
            if stage_idx < len(self.stages) - 1:
                logger.info(f"Waiting before next stage...")
                time.sleep(30)

        deployment_report["success"] = True
        logger.info(f"\n{'='*60}")
        logger.info("✓ Canary deployment completed successfully")
        logger.info(f"{'='*60}")

        # Save report
        with open("/tmp/canary_deployment_report.json", "w") as f:
            json.dump(deployment_report, f, indent=2)

        return True


class DeploymentMonitor:
    """Monitor ongoing deployment health."""

    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.check_interval = 60  # seconds
        self.alert_threshold = 5  # consecutive failures
        self.consecutive_failures = 0

    def check_deployment_health(self) -> bool:
        """Check overall deployment health."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                self.consecutive_failures = 0
                return True
            else:
                self.consecutive_failures += 1
                return False
        except Exception:
            self.consecutive_failures += 1
            return False

    def should_alert(self) -> bool:
        """Determine if alert should be triggered."""
        return self.consecutive_failures >= self.alert_threshold

    def run_continuous_monitoring(self, duration: int = 3600):
        """Run continuous monitoring for specified duration."""
        logger.info(f"Starting continuous monitoring for {duration} seconds...")

        start_time = time.time()
        while time.time() - start_time < duration:
            healthy = self.check_deployment_health()

            if healthy:
                logger.info("✓ Deployment healthy")
            else:
                logger.warning(
                    f"✗ Health check failed ({self.consecutive_failures}/{self.alert_threshold})"
                )

            if self.should_alert():
                logger.error("ALERT: Deployment unhealthy - triggering rollback")
                return False

            time.sleep(self.check_interval)

        logger.info("✓ Continuous monitoring completed")
        return True


def main():
    """Execute canary deployment."""
    logger.info("Canary Deployment Manager")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT')}")
    logger.info(f"API URL: {os.getenv('API_URL', 'http://localhost:8000')}")

    try:
        # Run canary deployment
        canary = CanaryDeployment()
        if not canary.run_canary_deployment():
            logger.error("Canary deployment failed")
            sys.exit(1)

        # Start continuous monitoring
        logger.info("\nStarting post-deployment monitoring...")
        monitor = DeploymentMonitor()
        if not monitor.run_continuous_monitoring(duration=3600):
            logger.error("Deployment monitoring detected issues")
            sys.exit(1)

        logger.info("✓ Deployment successful and stable")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
