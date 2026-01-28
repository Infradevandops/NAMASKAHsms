"""Load testing with Locust."""

from locust import HttpUser, between, task


class VerificationUser(HttpUser):
    """Simulates a user performing verification operations."""

    wait_time = between(1, 3)

    def on_start(self):
        """Called when a Locust user starts executing those tasks."""
        # Login or get token
        self.token = "test-token"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def get_services(self):
        """Get available services."""
        self.client.get("/api/v1/verify/services", headers=self.headers)

    @task(2)
    def get_history(self):
        """Get verification history."""
        self.client.get("/api/v1/verify/history?limit=50", headers=self.headers)

    @task(1)
    def health_check(self):
        """Check API health."""
        self.client.get("/health")


class AdminUser(HttpUser):
    """Simulates an admin user."""

    wait_time = between(2, 5)

    def on_start(self):
        """Called when a Locust user starts executing those tasks."""
        self.token = "admin-token"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(1)
    def get_dashboard(self):
        """Get admin dashboard."""
        self.client.get("/api/v1/admin/dashboard", headers=self.headers)

    @task(1)
    def get_analytics(self):
        """Get analytics."""
        self.client.get("/api/v1/admin/analytics", headers=self.headers)
