# Python Concurrency Workshop

A hands-on workshop on concurrency in Python: **threads, processes and asyncio**.
It has 200+ runnable examples, from "what is the GIL" up to building your own event loop.

Based on the source code of Matthew Fowler's *Concurrency in Python with Asyncio* (Manning), in
[concurrency-in-python-with-asyncio](https://github.com/concurrency-in-python-with-asyncio/concurrency-in-python-with-asyncio).
The style (descriptive file names, comments on each concept, a summary per chapter, FastAPI + Locust experiments) comes from
[JuanJFarina/python-concurrency-with-asyncio](https://github.com/JuanJFarina/python-concurrency-with-asyncio).

Changes from the book's code:

- Updated for **Python 3.12+**. Removed or deprecated APIs are replaced: `@asyncio.coroutine`, `get_event_loop()` inside coroutines,
  bare coroutines passed to `asyncio.wait`, Starlette `on_startup`, aiohttp string app keys, and the book's `numpy`/`Pool` memory hogs.
- Every file starts with a docstring that says **what the use case is**, **what to watch for**, and **how to run it**.
- Bug fixes: resource leaks, a crawler that failed on relative links, un-awaited `gather`, a wrongly placed `RLock`, and a subprocess deadlock that could not be recovered.
- Modern bonus examples: `TaskGroup`, `asyncio.timeout`, eager tasks, `uvloop.run`, Django async views in one file,
  and a FastAPI sync-vs-async benchmark chapter.

## Setup

```bash
# Python 3.12+ and uv (https://docs.astral.sh/uv/)
uv sync                      # install dependencies into .venv
docker compose up -d         # Postgres for chapters 5, 6.15, 8.11, 9, 10, 15
                             # port 5432 busy? -> export PGPORT=55432 first (the examples read PGPORT too)

# Create and seed the products database (once)
uv run python -m workshop.ch05_async_databases.02_create_schema
uv run python -m workshop.ch05_async_databases.04_insert_random_brands
uv run python -m workshop.ch05_async_databases.05_insert_random_products_and_skus

# Data for the MapReduce examples (chapter 6)
uv run python -m workshop.ch06_cpu_bound_multiprocessing.generate_ngrams_data
```

Run any example as a module from the repository root:

```bash
uv run python -m workshop.ch02_asyncio_basics.08_running_tasks_concurrently
uv run uvicorn workshop.ch15_fastapi_sync_vs_async.06_async_endpoint_async_io:app --port 8080
```

Other tools used by some examples: `nc` (netcat) or `telnet` for the socket servers, `gpg` for 13.7/13.8,
a display for the Tkinter apps (7.12, 7.15), and a Unix terminal for the chapter 8 console apps.

## Layout

```
workshop/
  common/                         delay(), @async_timed(), DB settings
  ch01_concurrency_basics/        processes, threads, GIL, I/O- vs CPU-bound
  ch02_asyncio_basics/            coroutines, tasks, futures, timeouts, pitfalls
  ch03_sockets_and_event_loop/    blocking → non-blocking → selectors → asyncio servers
  ch04_concurrent_web_requests/   aiohttp, gather, as_completed, wait
  ch05_async_databases/           asyncpg, pools, transactions, cursors, async generators
  ch06_cpu_bound_multiprocessing/ process pools, MapReduce, shared memory
  ch07_threads_and_blocking_io/   thread pools, to_thread, locks, deadlocks, GUI + asyncio
  ch08_streams/                   protocols, streams, async stdin, chat server/client
  ch09_web_applications/          aiohttp, WSGI vs ASGI, Flask, Starlette, WebSockets, Django
  ch10_microservices/             backend-for-frontend, retries, circuit breaker
  ch11_synchronization/           Lock, Semaphore, Event, Condition, race conditions
  ch12_queues/                    producer/consumer, job queues, crawler, priority queues
  ch13_subprocesses/              async subprocesses, pipes, interactive programs
  ch14_advanced_asyncio/          contextvars, uvloop, build your own Future/Task/event loop
  ch15_fastapi_sync_vs_async/     bonus: FastAPI def vs async def under load
locust/                           load tests (Locust) for the web examples
docker/initdb/                    Postgres databases for chapters 5, 9 and 10
```

Each chapter folder has a `README.md` with a table of every file (with its book listing number), the use case it
shows, the key takeaways and things to try.

## Which tool for which job

| Your workload | Use | Why | See |
|---|---|---|---|
| Many network/DB calls, async libraries available | **asyncio** | thousands of concurrent waits on one thread | ch2, ch4, ch5 |
| Blocking library you cannot replace (requests, boto3, psycopg2) | **threads** (`asyncio.to_thread`, `ThreadPoolExecutor`) | the GIL is released during I/O | ch7 |
| CPU-heavy pure Python | **processes** (`ProcessPoolExecutor`) | one GIL per process means real parallelism | ch6 |
| CPU-heavy C code that releases the GIL (numpy, hashlib, zlib) | **threads** | parallel without pickling overhead | 7.17, 7.19 |
| External CLI tools | **asyncio subprocesses** | the OS runs them in parallel | ch13 |
| Web API with I/O | **ASGI** (FastAPI/Starlette/aiohttp) + async drivers | many requests per worker | ch9, ch15 |
| Web API, sync ORM | **WSGI** + workers, or `def` endpoints in FastAPI | simple and predictable | 9.5, 15.07 |
| Scale an async service past one core | **several processes, each with an event loop** | `uvicorn --workers N` | 6.15, 15.10 |
| Free-threaded Python 3.13t/3.14t | threads for CPU work too | no GIL | 1.6 |

## All use cases, by problem

### Running things concurrently
- Run independent I/O waits at the same time: [2.9](workshop/ch02_asyncio_basics/08_running_tasks_concurrently.py), [2.10](workshop/ch02_asyncio_basics/09_running_code_while_waiting.py), [4.5](workshop/ch04_concurrent_web_requests/05_create_tasks_then_await.py)
- Fan out N HTTP requests and collect the results: [4.6](workshop/ch04_concurrent_web_requests/06_gather_many_requests.py), [4.7](workshop/ch04_concurrent_web_requests/07_gather_preserves_order.py)
- Show results as soon as each one is ready: [4.8](workshop/ch04_concurrent_web_requests/08_as_completed.py), [4.14](workshop/ch04_concurrent_web_requests/15_wait_first_completed_loop.py)
- First response wins (hedged requests): [4.13](workshop/ch04_concurrent_web_requests/14_wait_first_completed.py)
- All-or-nothing batch, cancel the rest on the first error: [4.12](workshop/ch04_concurrent_web_requests/13_wait_first_exception.py), [TaskGroup](workshop/ch02_asyncio_basics/23_task_group_modern.py)
- Keep partial successes and log the failures: [gather return_exceptions](workshop/ch04_concurrent_web_requests/10_gather_exceptions.py), [4.11](workshop/ch04_concurrent_web_requests/12_wait_handling_exceptions.py)
- Run DB queries concurrently: [5.7](workshop/ch05_async_databases/06_connection_pool_queries.py), [5.8](workshop/ch05_async_databases/07_pool_sequential_vs_concurrent.py)
- Aggregate several microservices into one response: [10.8](workshop/ch10_microservices/05_backend_for_frontend.py)

### Timeouts, cancellation, resilience
- Cancel a task: [2.11](workshop/ch02_asyncio_basics/10_cancelling_tasks.py) · Timeout: [2.12](workshop/ch02_asyncio_basics/11_timeout_with_wait_for.py), [4.3](workshop/ch04_concurrent_web_requests/03_aiohttp_timeouts.py), [4.15](workshop/ch04_concurrent_web_requests/16_wait_timeout.py), [4.9](workshop/ch04_concurrent_web_requests/09_as_completed_timeout.py)
- Warn the user but let the work finish: [2.13 shield](workshop/ch02_asyncio_basics/12_shield_from_cancellation.py)
- Drop only the slow optional call: [4.16](workshop/ch04_concurrent_web_requests/17_wait_cancel_slow_task.py)
- Retry transient failures: [10.10](workshop/ch10_microservices/06_retry.py) · Fail fast when a dependency is down: [10.12 circuit breaker](workshop/ch10_microservices/07_circuit_breaker.py)
- Graceful shutdown on SIGINT/SIGTERM: [3.9](workshop/ch03_sockets_and_event_loop/09_signal_handler.py), [3.10](workshop/ch03_sockets_and_event_loop/10_graceful_shutdown.py), [7.2](workshop/ch07_threads_and_blocking_io/02_threaded_echo_server_shutdown.py), [12.3](workshop/ch12_queues/03_web_app_order_queue.py)
- Kill a hung subprocess: [13.2](workshop/ch13_subprocesses/02_subprocess_timeout_terminate.py)

### Limiting concurrency and back-pressure
- Cap concurrent requests to an API: [11.7](workshop/ch11_synchronization/07_semaphore_rate_limit_requests.py), [bench.py](workshop/ch15_fastapi_sync_vs_async/bench.py)
- Cap concurrent subprocesses: [13.8](workshop/ch13_subprocesses/07_limit_subprocesses_semaphore.py)
- Bounded producer/consumer: [12.2](workshop/ch12_queues/02_queue_producer_consumer_bounded.py)
- Size DB connection pools: [5.7](workshop/ch05_async_databases/06_connection_pool_queries.py), [9.2](workshop/ch09_web_applications/02_aiohttp_db_pool_brands.py)

### CPU-bound work
- Parallel CPU work in processes: [6.1](workshop/ch06_cpu_bound_multiprocessing/01_parallel_processes.py), [6.4](workshop/ch06_cpu_bound_multiprocessing/04_process_pool_executor_map.py)
- CPU work from async code without blocking the loop: [6.5](workshop/ch06_cpu_bound_multiprocessing/05_process_pool_with_asyncio.py), [15.10](workshop/ch15_fastapi_sync_vs_async/10_cpu_bound_endpoint.py)
- Parallel data processing (MapReduce): [6.8](workshop/ch06_cpu_bound_multiprocessing/08_map_reduce_process_pool.py), [6.9](workshop/ch06_cpu_bound_multiprocessing/09_parallel_reduce.py)
- Progress reporting for a long parallel job: [6.14](workshop/ch06_cpu_bound_multiprocessing/14_map_reduce_with_progress.py)
- GIL-releasing libraries on threads: [7.17 hashlib](workshop/ch07_threads_and_blocking_io/15_hashing_thread_pool.py), [7.19 numpy](workshop/ch07_threads_and_blocking_io/17_numpy_mean_threads.py)
- One event loop per core: [6.15](workshop/ch06_cpu_bound_multiprocessing/15_multiple_event_loops_in_processes.py)

### Blocking code in an async world (and the reverse)
- Call a blocking library from asyncio: [7.5](workshop/ch07_threads_and_blocking_io/05_thread_pool_with_asyncio.py), [7.6](workshop/ch07_threads_and_blocking_io/06_default_executor.py), [7.7 to_thread](workshop/ch07_threads_and_blocking_io/07_asyncio_to_thread.py), [15.05](workshop/ch15_fastapi_sync_vs_async/05_async_endpoint_to_thread.py)
- Run asyncio next to a GUI or another framework's main loop: [7.15](workshop/ch07_threads_and_blocking_io/13_load_tester_app.py)
- Django: `sync_to_async` / `async_to_sync`: [9 Django](workshop/ch09_web_applications/10_django_async_views.py)
- Read stdin without blocking: [8.6](workshop/ch08_streams/04_async_stdin_reader.py)

### Network servers and clients
- TCP servers, from raw sockets to asyncio: [ch3](workshop/ch03_sockets_and_event_loop/README.md), [8.12](workshop/ch08_streams/07_echo_server_with_user_count.py)
- Speak a TCP protocol with streams: [8.3](workshop/ch08_streams/02_stream_reader_http_client.py) · with protocols: [8.2](workshop/ch08_streams/01_protocol_http_client.py)
- Real-time chat (broadcast + idle timeout): [8.13 server](workshop/ch08_streams/08_chat_server.py), [8.14 client](workshop/ch08_streams/09_chat_client.py)
- Web crawler: [12.4](workshop/ch12_queues/04_web_crawler.py)
- Thread-per-client server: [7.1](workshop/ch07_threads_and_blocking_io/01_threaded_echo_server.py)

### Web applications
- Async REST API with a DB pool: [9.1-9.4 aiohttp](workshop/ch09_web_applications/README.md), [9.8 Starlette](workshop/ch09_web_applications/08_starlette_brands.py), [15.09 FastAPI](workshop/ch15_fastapi_sync_vs_async/09_async_db_asyncpg.py)
- WSGI vs ASGI from first principles: [9.6](workshop/ch09_web_applications/06_raw_wsgi_app.py), [9.7](workshop/ch09_web_applications/07_raw_asgi_app.py)
- WebSockets push: [9.9](workshop/ch09_web_applications/09_starlette_websocket_counter.py)
- Background jobs from a web request: [12.3](workshop/ch12_queues/03_web_app_order_queue.py), with priorities [12.7](workshop/ch12_queues/07_web_app_priority_orders.py)
- Load testing: [locust/](locust/README.md), [bench.py](workshop/ch15_fastapi_sync_vs_async/bench.py)

### Databases
- Connect, CRUD, bulk insert: [5.1](workshop/ch05_async_databases/01_connect_to_postgres.py), [5.4](workshop/ch05_async_databases/03_insert_and_select.py), [5.5](workshop/ch05_async_databases/04_insert_random_brands.py)
- Transactions, rollback, savepoints: [5.9](workshop/ch05_async_databases/08_transaction.py), [5.10](workshop/ch05_async_databases/09_transaction_rollback.py), [5.11](workshop/ch05_async_databases/10_nested_transactions_savepoints.py), [5.12](workshop/ch05_async_databases/11_manual_transaction.py)
- Stream huge result sets: [5.15](workshop/ch05_async_databases/14_cursor_streaming.py), [5.16](workshop/ch05_async_databases/15_cursor_forward_fetch.py), [5.17](workshop/ch05_async_databases/16_async_generator_take.py)
- Interactive concurrent SQL console: [8.11](workshop/ch08_streams/06_async_sql_console.py)

### Shared state and coordination
- Protect shared state in asyncio: [11.4](workshop/ch11_synchronization/04_asyncio_lock.py), [11.5](workshop/ch11_synchronization/05_lock_protecting_shared_dict.py) · in threads: [7.8](workshop/ch07_threads_and_blocking_io/08_thread_lock_progress_counter.py), [7.10](workshop/ch07_threads_and_blocking_io/10_thread_safe_list.py) · in processes: [6.12](workshop/ch06_cpu_bound_multiprocessing/12_shared_memory_with_lock.py), [6.13](workshop/ch06_cpu_bound_multiprocessing/13_shared_state_in_pool_initializer.py)
- Wait until something is ready: [11.10 Event](workshop/ch11_synchronization/10_event.py), [11.12](workshop/ch11_synchronization/11_event_file_upload_server.py), [11.15 Condition](workshop/ch11_synchronization/14_condition_wait_for_state.py)
- Work queues with priorities / LIFO: [12.5-12.10](workshop/ch12_queues/README.md)
- Request-scoped context: [14.2 contextvars](workshop/ch14_advanced_asyncio/02_context_variables.py)

### Subprocesses
- Run, stream, time out, feed input, automate interactive CLIs: [ch13](workshop/ch13_subprocesses/README.md)

### Understanding the internals
- Selector loop by hand: [3.7](workshop/ch03_sockets_and_event_loop/07_selector_echo_server.py) · generators as coroutines: [14.6](workshop/ch14_advanced_asyncio/06_generators_interleaved.py), [14.7](workshop/ch14_advanced_asyncio/07_coroutine_send.py)
- Build a Future, a Task and an event loop, then run a server on them: [14.8-14.13](workshop/ch14_advanced_asyncio/README.md)
- Debug mode to find blocking code: [2.23](workshop/ch02_asyncio_basics/21_debug_mode.py), [2.24](workshop/ch02_asyncio_basics/22_slow_callback_duration.py)

## Pitfalls (each one has a runnable demo)

| Pitfall | Demo | Fix |
|---|---|---|
| Calling a coroutine without awaiting it | [2.2](workshop/ch02_asyncio_basics/02_coroutine_vs_function.py) | `await` it or `create_task` it |
| `await` in sequence ≠ concurrency | [2.7](workshop/ch02_asyncio_basics/06_sequential_awaits.py), [4.4](workshop/ch04_concurrent_web_requests/04_create_task_in_comprehension_pitfall.py) | create tasks first, or `gather` |
| CPU-bound code in a coroutine | [2.18](workshop/ch02_asyncio_basics/16_cpu_bound_in_coroutines.py), [2.19](workshop/ch02_asyncio_basics/17_cpu_bound_blocks_io_tasks.py) | process pool |
| Blocking library in a coroutine | [2.20](workshop/ch02_asyncio_basics/18_blocking_library_in_coroutine.py), [15.03](workshop/ch15_fastapi_sync_vs_async/03_async_endpoint_blocking_call_pitfall.py), [15.08](workshop/ch15_fastapi_sync_vs_async/08_async_endpoint_sync_db_pitfall.py) | async library or `to_thread` |
| `input()` in an async app | [8.4](workshop/ch08_streams/03_blocking_input_pitfall.py) | async stdin reader |
| Threads for CPU-bound Python | [1.6](workshop/ch01_concurrency_basics/06_cpu_bound_with_threads_gil.py) | processes |
| Blocking sockets with many clients | [3.3](workshop/ch03_sockets_and_event_loop/03_blocking_multiple_clients_broken.py) | selectors / asyncio |
| Race across an `await` | [11.2](workshop/ch11_synchronization/02_race_condition_across_await.py), [11.3](workshop/ch11_synchronization/03_race_on_shared_connections.py) | `asyncio.Lock` |
| Race on shared memory | [6.11](workshop/ch06_cpu_bound_multiprocessing/11_shared_memory_race_condition.py) | `get_lock()` |
| Re-entrant locking | [7.9](workshop/ch07_threads_and_blocking_io/09_reentrant_lock.py) | `RLock` |
| Deadlock | [7.11](workshop/ch07_threads_and_blocking_io/11_deadlock.py) | same lock order everywhere |
| Extra semaphore release | [11.8](workshop/ch11_synchronization/08_semaphore_extra_release_pitfall.py) | `BoundedSemaphore` |
| Events dropping triggers | [11.13](workshop/ch11_synchronization/12_event_missed_triggers.py) | a queue |
| Equal priorities come out in no fixed order | [12.8](workshop/ch12_queues/08_priority_queue_ties.py) | insertion counter |
| Unread subprocess PIPE | [13.5](workshop/ch13_subprocesses/04_pipe_deadlock_pitfall.py) | stream it or `communicate()` |
| Naive interactive subprocess I/O | [13.12](workshop/ch13_subprocesses/09_interactive_subprocess_naive.py) | wait for the prompt |

## Ports used

| Port | Examples |
|---|---|
| 5432 (`PGPORT`) | Postgres |
| 8000 | socket servers (ch3, ch4.1, ch7, ch8, ch14), Starlette/Flask (ch9), product service (ch10) |
| 8001-8003 | inventory / favorites / cart services (ch10) |
| 8080 | aiohttp apps (ch9, ch12), FastAPI apps (ch15, suggested) |
| 8089 | Locust UI |
| 9000 | BFF (ch10), file upload (11.12), contextvars/uvloop (ch14) |
