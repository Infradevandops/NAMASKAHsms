

from locust import HttpUser, between, task

class TierLoadTest(HttpUser):

    wait_time = between(1, 2)

    def on_start(self):

        response = self.client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None

        @task(5)
    def check_tier(self):

        if self.token:
            self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {self.token}"})

        @task(1)
    def access_gated_feature(self):

        if self.token:
            self.client.get("/api/keys", headers={"Authorization": f"Bearer {self.token}"})