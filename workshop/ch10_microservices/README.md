# Chapter 10: Microservices: backend-for-frontend, retries, circuit breakers

Prerequisites: the products DB from chapter 5. The `cart` and `favorites` databases are created by `docker/initdb` (listings 10.2, 10.3).

```bash
uv run python -m workshop.ch10_microservices.run_services          # services on :8000-8003
uv run python -m workshop.ch10_microservices.05_backend_for_frontend # BFF on :9000
curl localhost:9000/products/all
```

| File | Listing | Use case |
|---|---|---|
| `docker/initdb/01_databases.sql` | 10.2, 10.3 | Database per service: `cart`, `favorites` |
| `db_pool.py` | 10.4 | Reusable pool hooks, parameterized by database |
| `01_inventory_service.py` | 10.1 | A slow, flaky dependency (0-2 s latency) |
| `02_favorites_service.py` | 10.5 | Favorites service |
| `03_cart_service.py` | 10.6 | Cart service |
| `04_product_service.py` | 10.7 | Product service |
| `05_backend_for_frontend.py` | 10.8 | **Aggregate services concurrently with timeouts and graceful degradation** |
| `retry.py` + `06_retry.py` | 10.9, 10.10 | Retry with a per-attempt timeout |
| `circuit_breaker.py` + `07_circuit_breaker.py` | 10.11, 10.12 | Circuit breaker: fail fast while a dependency is down |
| `run_services.py` | – | Start the four services |

## Key takeaways

- Call independent services **concurrently** (`create_task` + `wait(timeout=...)`), so latency is the slowest call, not the sum.
- Separate **required** data (fail the request) from **optional** data (return `null`).
- Retries absorb short blips. Circuit breakers stop cascading failures when a dependency is really down.
