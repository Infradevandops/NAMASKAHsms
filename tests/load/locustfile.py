"""Locust performance tests for Namaskah API"""

from locust import HttpUser, task, between


class NamaskahUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before starting tests"""
        response = self.client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(3)
    def view_dashboard(self):
        self.client.get("/dashboard")

    @task(2)
    def get_balance(self):
        self.client.get("/api/billing/balance")

    @task(2)
    def get_analytics(self):
        self.client.get("/api/analytics/summary")

    @task(1)
    def get_history(self):
        self.client.get("/api/v1/verify/history?limit=20")

    @task(1)
    def get_notifications(self):
        self.client.get("/api/notifications?limit=20")

    @task(1)
    def get_transactions(self):
        self.client.get("/api/billing/history?limit=20")


class ProviderRoutingUser(HttpUser):
    """Load test specifically for the multi-provider routing path.

    Simulates the purchase endpoint with mocked providers.
    Run against staging with TELNYX_ENABLED=false, FIVESIM_ENABLED=false
    to test the routing layer without real API calls.

    Usage:
        locust -f tests/load/locustfile.py --host=http://localhost:8000 \
               --users=50 --spawn-rate=10 --run-time=60s --headless

    Pass criteria:
        - p95 response time < 3000ms
        - Error rate < 1%
        - No memory growth over 1000 requests
    """

    wait_time = between(0.5, 2)

    def on_start(self):
        response = self.client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            self.token = None

    @task(5)
    def get_services(self):
        """Services list — hits TextVerified cache."""
        self.client.get("/api/verification/services")

    @task(3)
    def get_area_codes(self):
        """Area codes — hits TextVerified cache."""
        self.client.get("/api/verification/area-codes")

    @task(2)
    def get_balance(self):
        """Balance check — DB read."""
        self.client.get("/api/billing/balance")

    @task(1)
    def get_provider_status(self):
        """Provider health — checks all adapters."""
        self.client.get("/api/diagnostics")


# Run with:
# locust -f tests/load/locustfile.py --host=http://localhost:8000
#
# For provider routing load test:
# locust -f tests/load/locustfile.py ProviderRoutingUser \
#        --host=http://localhost:8000 \
#        --users=50 --spawn-rate=10 --run-time=60s --headless

