"""Load testing with locust."""
from locust import HttpUser, task, between
import random


class VerificationUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_countries(self):
        self.client.get("/api/countries/")

    @task(2)
    def get_services(self):
        countries = ["US", "UK", "CA", "AU"]
        country = random.choice(countries)
        self.client.get(f"/api/countries/{country}/services")

    @task(1)
    def create_verification(self):
        countries = ["US", "UK", "CA"]
        services = ["telegram", "whatsapp", "google"]
        self.client.post(
            "/api/verify/create",
            json={
                "country": random.choice(countries),
                "service": random.choice(services)
            }
        )

    @task(2)
    def check_metrics(self):
        self.client.get("/metrics")

    @task(1)
    def health_check(self):
        self.client.get("/health")
