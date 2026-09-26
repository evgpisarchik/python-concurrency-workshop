# Load testing with Locust (optional)

Notebook 9 benchmarks every endpoint with `workshop/bench.py`. Use Locust when you want a live UI with RPS and
latency charts while you change the load.

```bash
uv sync --group load
uv run uvicorn workshop.web.fastapi_app:app --port 8901            # add --workers 4 to compare

ENDPOINT=/sleep/blocking-in-async uv run locust -f locust/fastapi_app.py
# several load-generator processes (one locust process is limited to one CPU core):
ENDPOINT=/db/async uv run python locust/load_test.py locust/fastapi_app.py 4
```

Open http://localhost:8089. Endpoints: `/sleep/{blocking-in-async,blocking-in-def,to-thread,non-blocking}`,
`/db/{sync-in-def,sync-in-async,async}`, `/cpu/{inline,thread,process}`.
