"""Load test GET /time (workshop/ch09_web_applications/01_aiohttp_time_endpoint.py)."""

from locust import FastHttpUser, task


class TimeUser(FastHttpUser):
    host = "http://127.0.0.1:8080"

    @task
    def get_time(self):
        self.client.get("/time")
