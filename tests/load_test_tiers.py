from locust import HttpUser, task, between

class TierLoadTest(HttpUser):
    wait_time = between(1, 2)
    
    def on_start(self):
        # Assumes /api/auth/login exists and works.
        response = self.client.post("/api/auth/login", json={
            "email": "pro@test.com",
            "password": "hashedpassword" # In real test need valid password or way to get token
        })
        # If login fails, this will error.
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None # Or handle
    
    @task(5)
    def check_tier(self):
        if hasattr(self, 'token') and self.token:
            self.client.get(
                "/api/user/tier",
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(1)
    def access_gated_feature(self):
        if hasattr(self, 'token') and self.token:
            self.client.get(
                "/api/keys",
                headers={"Authorization": f"Bearer {self.token}"}
            )
