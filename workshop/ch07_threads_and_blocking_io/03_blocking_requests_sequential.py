"""Listing 7.3: blocking HTTP requests, one after another (the baseline).

Use case: the baseline for 04 to 07.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.03_blocking_requests_sequential
"""

import requests


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


url = "https://www.example.com"
print(get_status_code(url))
print(get_status_code(url))
