# Chapter 9: Web applications: aiohttp, WSGI vs ASGI, Starlette, Django

Prerequisite for the DB endpoints: the products DB from chapter 5.

| File | Listing | Use case | Run |
|---|---|---|---|
| `01_aiohttp_time_endpoint.py` | 9.1 | Minimal async HTTP API | `uv run python -m workshop.ch09_web_applications.01_aiohttp_time_endpoint` |
| `aiohttp_db.py` + `02_aiohttp_db_pool_brands.py` | 9.2 | DB pool tied to the app lifecycle (`on_startup` / `on_cleanup`) | `python -m ...02_aiohttp_db_pool_brands` |
| `03_aiohttp_get_product.py` | 9.3 | Path params, 400/404 handling | `python -m ...03_aiohttp_get_product` |
| `04_aiohttp_create_product.py` | 9.4 | POST JSON body, 201 Created | `python -m ...04_aiohttp_create_product` |
| `05_flask_brands_wsgi.py` | 9.5 | Sync WSGI baseline to compare against | `uv run gunicorn -w 8 -b 127.0.0.1:8000 workshop.ch09_web_applications.05_flask_brands_wsgi:app` |
| `06_raw_wsgi_app.py` | 9.6 | What WSGI is: a sync callable | `uv run gunicorn workshop.ch09_web_applications.06_raw_wsgi_app:application` |
| `07_raw_asgi_app.py` | 9.7 | What ASGI is: an async callable exchanging events | `uv run uvicorn workshop.ch09_web_applications.07_raw_asgi_app:application` |
| `08_starlette_brands.py` | 9.8 | ASGI framework + lifespan-managed pool | `uv run uvicorn --workers 8 workshop.ch09_web_applications.08_starlette_brands:app` |
| `09_starlette_websocket_counter.py` + `websocket_counter.html` | 9.9, 9.10 | Real-time push with WebSockets | `uv run uvicorn workshop.ch09_web_applications.09_starlette_websocket_counter:app` |
| `10_django_async_views.py` | 9.4 (book section) | Django async views, `sync_to_async`, `async_to_sync` | `uv run uvicorn workshop.ch09_web_applications.10_django_async_views:app` |

## WSGI vs ASGI

| | WSGI | ASGI |
|---|---|---|
| Interface | `app(environ, start_response)`, sync | `async app(scope, receive, send)` |
| Concurrency | one request per worker thread/process | many requests per worker (event loop) |
| WebSockets / streaming / long polling | ❌ / limited | ✅ |
| Frameworks | Flask, Django (sync), Bottle, Pyramid | FastAPI, Starlette, Django 3+, Quart, Litestar |
| Servers | gunicorn, uWSGI, mod_wsgi | uvicorn, hypercorn, daphne, granian |

`aiohttp` is async-native but **not** ASGI: it ships its own server.

**Rules of thumb:** use ASGI for I/O-heavy APIs, fan-out to other services, WebSockets and streaming.
WSGI plus enough workers is still fine for classic CRUD apps with a sync ORM.

## Django: calling across the sync/async boundary

| Call from ↓ / to → | sync code | async code |
|---|---|---|
| **async view** | `sync_to_async(fn, thread_sensitive=...)` | `await` |
| **sync view** | call it | `async_to_sync(coro_fn)()` |

`thread_sensitive=True` (the default) runs every call on one shared thread, which is safe for the ORM but
serial. `False` uses a thread pool. Compare:
`curl "localhost:8000/requests/sync_to_async?sleep_time=1&num_calls=5&thread_sensitive=True"` (≈5 s) vs `False` (≈1 s).

## Try it

Load-test `/brands` on Flask+gunicorn vs Starlette+uvicorn with `locust/brands.py` and compare requests per second.
