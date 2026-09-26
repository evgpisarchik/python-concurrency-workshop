"""Load test GET /work, the endpoint every chapter 15 FastAPI app exposes."""

from locust import FastHttpUser, task


class WorkUser(FastHttpUser):
    host = "http://127.0.0.1:8080"

    @task
    def get_work(self):
        self.client.get("/work")
