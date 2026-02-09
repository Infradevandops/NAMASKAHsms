"""Locust performance tests for Namaskah API"""
from locust import HttpUser, task, between

class NamaskahUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tests"""
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(3)
    def view_dashboard(self):
        """Test dashboard page load"""
        self.client.get("/dashboard")
    
    @task(2)
    def get_balance(self):
        """Test balance API"""
        self.client.get("/api/billing/balance")
    
    @task(2)
    def get_analytics(self):
        """Test analytics API"""
        self.client.get("/api/analytics/summary")
    
    @task(1)
    def get_history(self):
        """Test verification history"""
        self.client.get("/api/v1/verify/history?limit=20")
    
    @task(1)
    def get_notifications(self):
        """Test notifications API"""
        self.client.get("/api/notifications?limit=20")
    
    @task(1)
    def get_transactions(self):
        """Test transactions API"""
        self.client.get("/api/billing/history?limit=20")

# Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000
