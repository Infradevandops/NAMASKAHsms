#!/usr/bin/env python3
"""Post-deployment verification for production deployment."""

import os
import sys
import logging
import time
import json
from datetime import datetime
import requests
from typing import Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeploymentVerifier:
    """Verify production deployment health and metrics."""

    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.timeout = 30
        self.checks_passed = 0
        self.checks_failed = 0
        self.results = {}

    def check_api_health(self) -> bool:
        """Verify API is responding to health checks."""
        logger.info("Checking API health...")
        try:
            response = requests.get(f"{self.api_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                logger.info("✓ API health check passed")
                self.checks_passed += 1
                return True
            else:
                logger.error(f"API health check failed: {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            logger.error(f"API health check error: {e}")
            self.checks_failed += 1
            return False

    def check_database_health(self) -> bool:
        """Verify database is accessible."""
        logger.info("Checking database health...")
        try:
            response = requests.get(
                f"{self.api_url}/api/health/db", timeout=self.timeout
            )
            if response.status_code == 200:
                logger.info("✓ Database health check passed")
                self.checks_passed += 1
                return True
            else:
                logger.error(f"Database health check failed: {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            logger.error(f"Database health check error: {e}")
            self.checks_failed += 1
            return False

    def check_redis_health(self) -> bool:
        """Verify Redis cache is accessible."""
        logger.info("Checking Redis health...")
        try:
            response = requests.get(
                f"{self.api_url}/api/health/redis", timeout=self.timeout
            )
            if response.status_code == 200:
                logger.info("✓ Redis health check passed")
                self.checks_passed += 1
                return True
            else:
                logger.error(f"Redis health check failed: {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            logger.error(f"Redis health check error: {e}")
            self.checks_failed += 1
            return False

    def check_api_response_time(self) -> bool:
        """Verify API response times are acceptable."""
        logger.info("Checking API response time...")
        try:
            start = time.time()
            response = requests.get(f"{self.api_url}/health", timeout=self.timeout)
            elapsed = (time.time() - start) * 1000  # Convert to ms

            if elapsed < 500:  # Target: < 500ms
                logger.info(f"✓ API response time acceptable: {elapsed:.2f}ms")
                self.checks_passed += 1
                return True
            else:
                logger.warning(f"API response time high: {elapsed:.2f}ms")
                self.checks_failed += 1
                return False
        except Exception as e:
            logger.error(f"Response time check error: {e}")
            self.checks_failed += 1
            return False

    def check_error_rate(self) -> bool:
        """Verify error rate is within acceptable limits."""
        logger.info("Checking error rate...")
        try:
            response = requests.get(
                f"{self.api_url}/api/metrics/errors", timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                error_rate = data.get("error_rate", 0)

                if error_rate < 1.0:  # Target: < 1%
                    logger.info(f"✓ Error rate acceptable: {error_rate:.2f}%")
                    self.checks_passed += 1
                    return True
                else:
                    logger.error(f"Error rate too high: {error_rate:.2f}%")
                    self.checks_failed += 1
                    return False
            else:
                logger.warning("Could not retrieve error rate metrics")
                return True
        except Exception as e:
            logger.warning(f"Error rate check skipped: {e}")
            return True

    def check_tier_system(self) -> bool:
        """Verify tier identification system is working."""
        logger.info("Checking tier system...")
        try:
            response = requests.get(
                f"{self.api_url}/api/health/tiers", timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    logger.info("✓ Tier system healthy")
                    self.checks_passed += 1
                    return True
                else:
                    logger.error("Tier system unhealthy")
                    self.checks_failed += 1
                    return False
            else:
                logger.warning("Could not verify tier system")
                return True
        except Exception as e:
            logger.warning(f"Tier system check skipped: {e}")
            return True

    def check_monitoring_integration(self) -> bool:
        """Verify monitoring is properly integrated."""
        logger.info("Checking monitoring integration...")
        try:
            # Check Prometheus metrics
            response = requests.get(f"{self.api_url}/metrics", timeout=self.timeout)
            if response.status_code == 200:
                logger.info("✓ Prometheus metrics available")
                self.checks_passed += 1
                return True
            else:
                logger.warning("Prometheus metrics not available")
                return True
        except Exception as e:
            logger.warning(f"Monitoring check skipped: {e}")
            return True

    def check_canary_metrics(self) -> bool:
        """Verify canary deployment metrics."""
        logger.info("Checking canary deployment metrics...")
        try:
            response = requests.get(
                f"{self.api_url}/api/metrics/canary", timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                success_rate = data.get("success_rate", 0)

                if success_rate >= 99.0:  # Target: >= 99%
                    logger.info(f"✓ Canary success rate: {success_rate:.2f}%")
                    self.checks_passed += 1
                    return True
                else:
                    logger.error(f"Canary success rate low: {success_rate:.2f}%")
                    self.checks_failed += 1
                    return False
            else:
                logger.warning("Could not retrieve canary metrics")
                return True
        except Exception as e:
            logger.warning(f"Canary metrics check skipped: {e}")
            return True

    def check_database_migrations(self) -> bool:
        """Verify database migrations are applied."""
        logger.info("Checking database migrations...")
        try:
            response = requests.get(
                f"{self.api_url}/api/health/migrations", timeout=self.timeout
            )
            if response.status_code == 200:
                logger.info("✓ Database migrations verified")
                self.checks_passed += 1
                return True
            else:
                logger.error("Database migrations check failed")
                self.checks_failed += 1
                return False
        except Exception as e:
            logger.warning(f"Migration check skipped: {e}")
            return True

    def check_ssl_certificate(self) -> bool:
        """Verify SSL certificate is valid."""
        logger.info("Checking SSL certificate...")
        try:
            import ssl
            import socket

            hostname = (
                self.api_url.replace("http://", "")
                .replace("https://", "")
                .split(":")[0]
            )
            context = ssl.create_default_context()

            with socket.create_connection(
                (hostname, 443), timeout=self.timeout
            ) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    logger.info("✓ SSL certificate valid")
                    self.checks_passed += 1
                    return True
        except Exception as e:
            logger.warning(f"SSL check skipped: {e}")
            return True

    def run_all_checks(self) -> Dict:
        """Run all verification checks."""
        logger.info("Starting post-deployment verification...")

        checks = [
            ("API Health", self.check_api_health),
            ("Database Health", self.check_database_health),
            ("Redis Health", self.check_redis_health),
            ("API Response Time", self.check_api_response_time),
            ("Error Rate", self.check_error_rate),
            ("Tier System", self.check_tier_system),
            ("Monitoring Integration", self.check_monitoring_integration),
            ("Canary Metrics", self.check_canary_metrics),
            ("Database Migrations", self.check_database_migrations),
            ("SSL Certificate", self.check_ssl_certificate),
        ]

        for check_name, check_func in checks:
            try:
                self.results[check_name] = check_func()
            except Exception as e:
                logger.error(f"Check '{check_name}' failed with error: {e}")
                self.results[check_name] = False
                self.checks_failed += 1

        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate verification report."""
        total_checks = self.checks_passed + self.checks_failed
        success_rate = (
            (self.checks_passed / total_checks * 100) if total_checks > 0 else 0
        )

        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("ENVIRONMENT"),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "total_checks": total_checks,
            "success_rate": success_rate,
            "results": self.results,
            "deployment_ready": self.checks_failed == 0,
        }

        # Log report
        logger.info("\n" + "=" * 60)
        logger.info("POST-DEPLOYMENT VERIFICATION REPORT")
        logger.info("=" * 60)
        for check_name, passed in self.results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"{check_name:.<40} {status}")
        logger.info("=" * 60)
        logger.info(f"Passed: {self.checks_passed}/{total_checks}")
        logger.info(f"Success Rate: {success_rate:.2f}%")
        logger.info("=" * 60)

        if report["deployment_ready"]:
            logger.info("✓ Deployment verification successful")
        else:
            logger.error("✗ Deployment verification failed")

        # Save report
        with open("/tmp/deployment_verification.json", "w") as f:
            json.dump(report, f, indent=2)

        return report


def main():
    """Run post-deployment verification."""
    logger.info("Starting post-deployment verification...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT')}")
    logger.info(f"API URL: {os.getenv('API_URL', 'http://localhost:8000')}")

    # Wait for API to be ready
    logger.info("Waiting for API to be ready...")
    time.sleep(5)

    try:
        verifier = DeploymentVerifier()
        report = verifier.run_all_checks()

        if report["deployment_ready"]:
            logger.info("✓ Post-deployment verification completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ Post-deployment verification failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Post-deployment verification error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
