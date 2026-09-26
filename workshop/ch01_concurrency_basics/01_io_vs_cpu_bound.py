"""Listing 1.1: telling I/O-bound work apart from CPU-bound work.

Use case: before choosing a concurrency tool, classify each step of your program.
    * I/O-bound  -> waiting for network, disk, database (asyncio or threads help)
    * CPU-bound  -> the processor is busy computing (only processes help, because of the GIL)

Run: uv run python -m workshop.ch01_concurrency_basics.01_io_vs_cpu_bound
"""

import requests

# I/O-bound: most of the time is spent waiting for the remote server.
response = requests.get("https://www.example.com")

# CPU-bound: pure Python processing of data already in memory.
items = response.headers.items()
headers = [f"{key}: {header}" for key, header in items]
formatted_headers = "\n".join(headers)

# I/O-bound: waiting for the disk.
with open("headers.txt", "w") as file:
    file.write(formatted_headers)

print(formatted_headers)
