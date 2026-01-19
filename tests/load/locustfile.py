"""
Locust Load Testing Configuration
"""

import json

from locust import HttpUser, between, task


class NamaskahUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before starting tasks."""
        response = self.client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "test_password"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            self.token = None

    @task(3)
    def view_homepage(self):
        """Load homepage."""
        self.client.get("/")

    @task(2)
    def check_health(self):
        """Check health endpoint."""
        self.client.get("/health")

    @task(2)
    def view_dashboard(self):
        """View dashboard (authenticated)."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.get("/dashboard", headers=headers)

    @task(1)
    def api_diagnostics(self):
        """Check diagnostics."""
        self.client.get("/api/diagnostics")

    @task(1)
    def list_countries(self):
        """List available countries."""
        self.client.get("/api/countries")
