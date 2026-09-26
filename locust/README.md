# Load testing with Locust

Install the optional group once:

```bash
uv sync --group load
```

Start the server you want to test, then:

```bash
# one process (simple)
uv run locust -f locust/work.py
# several processes (Linux/macOS/WSL)
uv run locust -f locust/work.py --processes 4
# master + workers, works everywhere
uv run python locust/load_test.py locust/work.py 4
# headless: 500 users, spawn 50/s, 30 s
uv run locust -f locust/work.py --headless -u 500 -r 50 -t 30s
```

Open http://localhost:8089 to start a test and watch RPS and latency.

| Locustfile | Target | Server examples |
|---|---|---|
| `time.py` | `GET :8080/time` | ch09 `01_aiohttp_time_endpoint` |
| `brands.py` | `GET :8000/brands` | ch09 `05_flask_brands_wsgi` (gunicorn), `08_starlette_brands` (uvicorn) |
| `work.py` | `GET :8080/work` | every ch15 FastAPI app |

For a quick comparison without Locust, use the asyncio benchmark in chapter 15:
`uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work -n 2000 -c 100`
