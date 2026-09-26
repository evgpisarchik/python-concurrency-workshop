"""Load test GET /brands. Compare Flask+gunicorn (9.5) with Starlette+uvicorn (9.8) and aiohttp (9.2)."""

from locust import FastHttpUser, task


class BrandsUser(FastHttpUser):
    host = "http://127.0.0.1:8000"

    @task
    def get_brands(self):
        self.client.get("/brands")
