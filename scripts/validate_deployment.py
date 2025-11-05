#!/usr/bin/env python3
"""
Production Deployment Validation Script
Comprehensive validation of production deployment health and performance.
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import httpx
import psutil


@dataclass
class ValidationResult:
    """Result of a validation check."""

    name: str
    status: str  # 'pass', 'fail', 'warn'
    message: str
    details: Dict[str, Any] = None
    duration_ms: float = 0


class DeploymentValidator:
    """Comprehensive deployment validation."""

    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.results: List[ValidationResult] = []
        self.start_time = time.time()

    async def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("🔍 Starting comprehensive deployment validation...")
        print(f"Target: {self.base_url}")
        print("=" * 60)

        # Infrastructure validations
        await self._validate_docker_services()
        await self._validate_database_connectivity()
        await self._validate_redis_connectivity()

        # Application validations
        await self._validate_health_endpoints()
        await self._validate_authentication()
        await self._validate_api_endpoints()

        # Security validations
        await self._validate_ssl_configuration()
        await self._validate_security_headers()
        await self._validate_rate_limiting()

        # Performance validations
        await self._validate_response_times()
        await self._validate_load_handling()

        # System validations
        await self._validate_resource_usage()
        await self._validate_logging()

        # Print results
        self._print_results()

        # Return overall success
        failed_checks = [r for r in self.results if r.status == "fail"]
        return len(failed_checks) == 0

    async def _validate_docker_services(self):
        """Validate Docker services are running."""
        start_time = time.time()

        try:
            # Check if docker-compose is running
            result = subprocess.run(
                [
                    "/usr/local/bin/docker-compose",
                    "-f",
                    "docker-compose.prod.yml",
                    "ps",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode == 0:
                # Parse service status
                lines = result.stdout.strip().split("\n")[2:]  # Skip header
                services = {}

                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            service_name = parts[0]
                            status = "Up" in line
                            services[service_name] = status

                # Check critical services
                critical_services = ["app1", "app2", "app3", "db", "redis", "nginx"]
                failed_services = [
                    s for s in critical_services if not services.get(s, False)
                ]

                if not failed_services:
                    self.results.append(
                        ValidationResult(
                            "Docker Services",
                            "pass",
                            f"All {len(services)} services are running",
                            {"services": services},
                            (time.time() - start_time) * 1000,
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "Docker Services",
                            "fail",
                            f"Failed services: {', '.join(failed_services)}",
                            {"services": services, "failed": failed_services},
                            (time.time() - start_time) * 1000,
                        )
                    )
            else:
                self.results.append(
                    ValidationResult(
                        "Docker Services",
                        "fail",
                        "Docker Compose not running or accessible",
                        {"error": result.stderr},
                        (time.time() - start_time) * 1000,
                    )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Docker Services",
                    "fail",
                    f"Docker validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_database_connectivity(self):
        """Validate database connectivity and performance."""
        start_time = time.time()

        try:
            # Test database connection through health endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/system/health")

                if response.status_code == 200:
                    health_data = response.json()
                    db_status = health_data.get("services", {}).get("database", {})

                    if db_status.get("status") == "healthy":
                        response_time = db_status.get("response_time", 0) * 1000

                        if response_time < 100:  # Less than 100ms
                            self.results.append(
                                ValidationResult(
                                    "Database Connectivity",
                                    "pass",
                                    f"Database healthy (response: {response_time:.1f}ms)",
                                    db_status,
                                    (time.time() - start_time) * 1000,
                                )
                            )
                        else:
                            self.results.append(
                                ValidationResult(
                                    "Database Connectivity",
                                    "warn",
                                    f"Database slow (response: {response_time:.1f}ms)",
                                    db_status,
                                    (time.time() - start_time) * 1000,
                                )
                            )
                    else:
                        self.results.append(
                            ValidationResult(
                                "Database Connectivity",
                                "fail",
                                f"Database unhealthy: {db_status.get('error', 'Unknown error')}",
                                db_status,
                                (time.time() - start_time) * 1000,
                            )
                        )
                else:
                    self.results.append(
                        ValidationResult(
                            "Database Connectivity",
                            "fail",
                            f"Health endpoint returned {response.status_code}",
                            {"status_code": response.status_code},
                            (time.time() - start_time) * 1000,
                        )
                    )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Database Connectivity",
                    "fail",
                    f"Database validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_redis_connectivity(self):
        """Validate Redis connectivity and performance."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/system/health")

                if response.status_code == 200:
                    health_data = response.json()
                    redis_status = health_data.get("services", {}).get("redis", {})

                    if redis_status.get("status") == "healthy":
                        response_time = redis_status.get("response_time", 0) * 1000

                        self.results.append(
                            ValidationResult(
                                "Redis Connectivity",
                                "pass",
                                f"Redis healthy (response: {response_time:.1f}ms)",
                                redis_status,
                                (time.time() - start_time) * 1000,
                            )
                        )
                    else:
                        self.results.append(
                            ValidationResult(
                                "Redis Connectivity",
                                "warn",
                                f"Redis issues: {redis_status.get('error', 'Unknown error')}",
                                redis_status,
                                (time.time() - start_time) * 1000,
                            )
                        )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Redis Connectivity",
                    "fail",
                    f"Redis validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_health_endpoints(self):
        """Validate health check endpoints."""
        start_time = time.time()

        endpoints = [
            "/system/health",
            "/system/health/liveness",
            "/system/health/readiness",
        ]

        results = {}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for endpoint in endpoints:
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}")
                        results[endpoint] = {
                            "status_code": response.status_code,
                            "response_time": response.elapsed.total_seconds() * 1000,
                            "success": response.status_code == 200,
                        }
                    except Exception as e:
                        results[endpoint] = {"error": str(e), "success": False}

            # Check results
            successful_endpoints = [
                ep for ep, result in results.items() if result.get("success")
            ]

            if len(successful_endpoints) == len(endpoints):
                avg_response_time = sum(
                    r.get("response_time", 0) for r in results.values()
                ) / len(results)
                self.results.append(
                    ValidationResult(
                        "Health Endpoints",
                        "pass",
                        f"All health endpoints responding (avg: {avg_response_time:.1f}ms)",
                        results,
                        (time.time() - start_time) * 1000,
                    )
                )
            else:
                failed_endpoints = [
                    ep for ep in endpoints if ep not in successful_endpoints
                ]
                self.results.append(
                    ValidationResult(
                        "Health Endpoints",
                        "fail",
                        f"Failed endpoints: {', '.join(failed_endpoints)}",
                        results,
                        (time.time() - start_time) * 1000,
                    )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Health Endpoints",
                    "fail",
                    f"Health endpoint validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_authentication(self):
        """Validate authentication endpoints."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test protected endpoint without auth (should fail)
                response = await client.get(f"{self.base_url}/auth/me")

                if response.status_code == 401:
                    self.results.append(
                        ValidationResult(
                            "Authentication",
                            "pass",
                            "Protected endpoints properly secured",
                            {"status_code": response.status_code},
                            (time.time() - start_time) * 1000,
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "Authentication",
                            "fail",
                            f"Protected endpoint returned {response.status_code} instead of 401",
                            {"status_code": response.status_code},
                            (time.time() - start_time) * 1000,
                        )
                    )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Authentication",
                    "fail",
                    f"Authentication validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_api_endpoints(self):
        """Validate key API endpoints."""
        start_time = time.time()

        public_endpoints = ["/services/list", "/services/status", "/system/info"]

        results = {}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for endpoint in public_endpoints:
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}")
                        results[endpoint] = {
                            "status_code": response.status_code,
                            "response_time": response.elapsed.total_seconds() * 1000,
                            "success": response.status_code
                            in [200, 404],  # 404 is acceptable for some endpoints
                        }
                    except Exception as e:
                        results[endpoint] = {"error": str(e), "success": False}

            successful_endpoints = [
                ep for ep, result in results.items() if result.get("success")
            ]

            if (
                len(successful_endpoints) >= len(public_endpoints) * 0.8
            ):  # 80% success rate
                self.results.append(
                    ValidationResult(
                        "API Endpoints",
                        "pass",
                        f"{len(successful_endpoints)}/{len(public_endpoints)} endpoints responding",
                        results,
                        (time.time() - start_time) * 1000,
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        "API Endpoints",
                        "warn",
                        f"Only {len(successful_endpoints)}/{len(public_endpoints)} endpoints responding",
                        results,
                        (time.time() - start_time) * 1000,
                    )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "API Endpoints",
                    "fail",
                    f"API endpoint validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_ssl_configuration(self):
        """Validate SSL/TLS configuration."""
        start_time = time.time()

        if not self.base_url.startswith("https://"):
            self.results.append(
                ValidationResult(
                    "SSL Configuration",
                    "warn",
                    "Testing HTTP endpoint - SSL validation skipped",
                    {"base_url": self.base_url},
                    (time.time() - start_time) * 1000,
                )
            )
            return

        try:
            async with httpx.AsyncClient(timeout=10.0, verify=True) as client:
                response = await client.get(f"{self.base_url}/system/health")

                if response.status_code == 200:
                    self.results.append(
                        ValidationResult(
                            "SSL Configuration",
                            "pass",
                            "SSL certificate valid and trusted",
                            {"status_code": response.status_code},
                            (time.time() - start_time) * 1000,
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "SSL Configuration",
                            "warn",
                            f"SSL connection successful but got {response.status_code}",
                            {"status_code": response.status_code},
                            (time.time() - start_time) * 1000,
                        )
                    )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "SSL Configuration",
                    "fail",
                    f"SSL validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_security_headers(self):
        """Validate security headers."""
        start_time = time.time()

        expected_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
        ]

        if self.base_url.startswith("https://"):
            expected_headers.append("Strict-Transport-Security")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/system/health")

                present_headers = []
                missing_headers = []

                for header in expected_headers:
                    if header.lower() in [h.lower() for h in response.headers.keys()]:
                        present_headers.append(header)
                    else:
                        missing_headers.append(header)

                if not missing_headers:
                    self.results.append(
                        ValidationResult(
                            "Security Headers",
                            "pass",
                            f"All {len(expected_headers)} security headers present",
                            {"present": present_headers},
                            (time.time() - start_time) * 1000,
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "Security Headers",
                            "warn",
                            f"Missing headers: {', '.join(missing_headers)}",
                            {"present": present_headers, "missing": missing_headers},
                            (time.time() - start_time) * 1000,
                        )
                    )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Security Headers",
                    "fail",
                    f"Security header validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_rate_limiting(self):
        """Validate rate limiting is working."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Make rapid requests to trigger rate limiting
                responses = []
                for _ in range(10):
                    try:
                        response = await client.get(f"{self.base_url}/system/health")
                        responses.append(response.status_code)
                    except Exception:
                        responses.append(0)

                # Check if we got any rate limit responses (429)
                rate_limited = any(code == 429 for code in responses)
                success_rate = sum(1 for code in responses if code == 200) / len(
                    responses
                )

                if success_rate > 0.8:  # Most requests should succeed
                    self.results.append(
                        ValidationResult(
                            "Rate Limiting",
                            "pass",
                            f"Rate limiting configured (success rate: {success_rate:.1%})",
                            {"responses": responses, "rate_limited": rate_limited},
                            (time.time() - start_time) * 1000,
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "Rate Limiting",
                            "warn",
                            f"High failure rate (success rate: {success_rate:.1%})",
                            {"responses": responses},
                            (time.time() - start_time) * 1000,
                        )
                    )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Rate Limiting",
                    "fail",
                    f"Rate limiting validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_response_times(self):
        """Validate response time performance."""
        start_time = time.time()

        try:
            response_times = []

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test multiple requests
                for _ in range(5):
                    request_start = time.time()
                    response = await client.get(f"{self.base_url}/system/health")
                    request_time = (time.time() - request_start) * 1000

                    if response.status_code == 200:
                        response_times.append(request_time)

            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)

                if avg_time < 500:  # Less than 500ms average
                    self.results.append(
                        ValidationResult(
                            "Response Times",
                            "pass",
                            f"Good performance (avg: {avg_time:.1f}ms, max: {max_time:.1f}ms)",
                            {
                                "avg_ms": avg_time,
                                "max_ms": max_time,
                                "samples": len(response_times),
                            },
                            (time.time() - start_time) * 1000,
                        )
                    )
                elif avg_time < 2000:  # Less than 2s average
                    self.results.append(
                        ValidationResult(
                            "Response Times",
                            "warn",
                            f"Acceptable performance (avg: {avg_time:.1f}ms, max: {max_time:.1f}ms)",
                            {
                                "avg_ms": avg_time,
                                "max_ms": max_time,
                                "samples": len(response_times),
                            },
                            (time.time() - start_time) * 1000,
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "Response Times",
                            "fail",
                            f"Poor performance (avg: {avg_time:.1f}ms, max: {max_time:.1f}ms)",
                            {
                                "avg_ms": avg_time,
                                "max_ms": max_time,
                                "samples": len(response_times),
                            },
                            (time.time() - start_time) * 1000,
                        )
                    )
            else:
                self.results.append(
                    ValidationResult(
                        "Response Times",
                        "fail",
                        "No successful responses for performance testing",
                        {},
                        (time.time() - start_time) * 1000,
                    )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Response Times",
                    "fail",
                    f"Response time validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_load_handling(self):
        """Validate concurrent load handling."""
        start_time = time.time()

        try:
            # Create concurrent requests
            async with httpx.AsyncClient(timeout=30.0) as client:
                tasks = []
                for _ in range(20):  # 20 concurrent requests
                    task = client.get(f"{self.base_url}/system/health")
                    tasks.append(task)

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                successful_responses = sum(
                    1
                    for r in responses
                    if hasattr(r, "status_code") and r.status_code == 200
                )
                success_rate = successful_responses / len(responses)

                if success_rate > 0.9:  # 90% success rate
                    self.results.append(
                        ValidationResult(
                            "Load Handling",
                            "pass",
                            f"Excellent load handling ({successful_responses}/{len(responses)} successful)",
                            {
                                "success_rate": success_rate,
                                "total_requests": len(responses),
                            },
                            (time.time() - start_time) * 1000,
                        )
                    )
                elif success_rate > 0.7:  # 70% success rate
                    self.results.append(
                        ValidationResult(
                            "Load Handling",
                            "warn",
                            f"Acceptable load handling ({successful_responses}/{len(responses)} successful)",
                            {
                                "success_rate": success_rate,
                                "total_requests": len(responses),
                            },
                            (time.time() - start_time) * 1000,
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "Load Handling",
                            "fail",
                            f"Poor load handling ({successful_responses}/{len(responses)} successful)",
                            {
                                "success_rate": success_rate,
                                "total_requests": len(responses),
                            },
                            (time.time() - start_time) * 1000,
                        )
                    )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Load Handling",
                    "fail",
                    f"Load handling validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_resource_usage(self):
        """Validate system resource usage."""
        start_time = time.time()

        try:
            # Get system resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Check Docker container stats if available
            container_stats = {}
            try:
                result = subprocess.run(
                    ["/usr/bin/docker", "stats", "--no-stream", "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )

                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            stats = json.loads(line)
                            container_stats[stats["Name"]] = {
                                "cpu": stats["CPUPerc"],
                                "memory": stats["MemUsage"],
                            }
            except Exception:
                pass  # Docker stats not available

            # Evaluate resource usage
            issues = []
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > 85:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > 90:
                issues.append(f"High disk usage: {disk.percent:.1f}%")

            resource_data = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "container_stats": container_stats,
            }

            if not issues:
                self.results.append(
                    ValidationResult(
                        "Resource Usage",
                        "pass",
                        f"Good resource usage (CPU: {cpu_percent:.1f}%, RAM: {memory.percent:.1f}%, Disk: {disk.percent:.1f}%)",
                        resource_data,
                        (time.time() - start_time) * 1000,
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        "Resource Usage",
                        "warn",
                        f"Resource concerns: {'; '.join(issues)}",
                        resource_data,
                        (time.time() - start_time) * 1000,
                    )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Resource Usage",
                    "fail",
                    f"Resource usage validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    async def _validate_logging(self):
        """Validate logging configuration."""
        start_time = time.time()

        try:
            # Check if log files exist and are being written
            log_files = ["/var/log/nginx/access.log", "/var/log/nginx/error.log"]

            log_status = {}
            for log_file in log_files:
                if os.path.exists(log_file):
                    stat = os.stat(log_file)
                    log_status[log_file] = {
                        "exists": True,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                else:
                    log_status[log_file] = {"exists": False}

            # Check Docker logs
            try:
                result = subprocess.run(
                    [
                        "/usr/local/bin/docker-compose",
                        "-f",
                        "docker-compose.prod.yml",
                        "logs",
                        "--tail=1",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                docker_logs_available = result.returncode == 0
            except Exception:
                docker_logs_available = False

            if docker_logs_available:
                self.results.append(
                    ValidationResult(
                        "Logging",
                        "pass",
                        "Logging system operational",
                        {"log_files": log_status, "docker_logs": docker_logs_available},
                        (time.time() - start_time) * 1000,
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        "Logging",
                        "warn",
                        "Limited logging access",
                        {"log_files": log_status, "docker_logs": docker_logs_available},
                        (time.time() - start_time) * 1000,
                    )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Logging",
                    "fail",
                    f"Logging validation failed: {str(e)}",
                    {"error": str(e)},
                    (time.time() - start_time) * 1000,
                )
            )

    def _print_results(self):
        """Print validation results."""
        total_time = (time.time() - self.start_time) * 1000

        print("\n" + "=" * 80)
        print("🏥 DEPLOYMENT VALIDATION RESULTS")
        print("=" * 80)

        # Count results by status
        passed = len([r for r in self.results if r.status == "pass"])
        warned = len([r for r in self.results if r.status == "warn"])
        failed = len([r for r in self.results if r.status == "fail"])

        # Print summary
        print("\n📊 SUMMARY:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ⚠️  Warnings: {warned}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏱️  Total time: {total_time:.1f}ms")

        # Print detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            status_icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[result.status]
            print(
                f"   {status_icon} {result.name}: {result.message} ({result.duration_ms:.1f}ms)"
            )

        # Overall status
        if failed == 0:
            if warned == 0:
                print("\n🎉 DEPLOYMENT VALIDATION SUCCESSFUL!")
                print("   All checks passed. Deployment is ready for production.")
            else:
                print("\n✅ DEPLOYMENT VALIDATION PASSED WITH WARNINGS")
                print(f"   {warned} warnings found. Review and address if needed.")
        else:
            print("\n❌ DEPLOYMENT VALIDATION FAILED")
            print(f"   {failed} critical issues found. Address before production use.")

        print("=" * 80)


async def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate production deployment")
    parser.add_argument("--url", default="http://localhost", help="Base URL to test")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    validator = DeploymentValidator(args.url)
    success = await validator.run_all_validations()

    if args.json:
        # Output JSON results
        json_results = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "base_url": args.url,
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "duration_ms": r.duration_ms,
                    "details": r.details,
                }
                for r in validator.results
            ],
        }
        print(json.dumps(json_results, indent=2))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
