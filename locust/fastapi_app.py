"""Load test one endpoint of workshop/web/fastapi_app.py.

uv run uvicorn workshop.web.fastapi_app:app --port 8901
ENDPOINT=/sleep/blocking-in-async uv run locust -f locust/fastapi_app.py
"""

import os

from locust import FastHttpUser, task

ENDPOINT = os.getenv("ENDPOINT", "/sleep/non-blocking")


class EndpointUser(FastHttpUser):
    host = "http://127.0.0.1:8901"

    @task
    def hit(self):
        self.client.get(ENDPOINT)
