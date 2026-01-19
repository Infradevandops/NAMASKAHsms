"""
Sustained Load Test - 10 minute test with 500 users
"""
from locust import HttpUser, task, between, events
import logging

logger = logging.getLogger(__name__)


class SustainedLoadUser(HttpUser):
    wait_time = between(2, 5)
    
    @task(5)
    def health_check(self):
        """Continuous health monitoring."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(3)
    def api_endpoints(self):
        """Test various API endpoints."""
        endpoints = [
            "/api/diagnostics",
            "/api/countries",
            "/api/v1/health"
        ]
        for endpoint in endpoints:
            self.client.get(endpoint)
    
    @task(1)
    def homepage(self):
        """Load homepage."""
        self.client.get("/")


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Log final stats on test completion."""
    if environment.stats.total.fail_ratio > 0.05:
        logger.error(f"❌ Test failed with {environment.stats.total.fail_ratio*100:.1f}% error rate")
        environment.process_exit_code = 1
    else:
        logger.info(f"✅ Test passed with {environment.stats.total.fail_ratio*100:.1f}% error rate")
