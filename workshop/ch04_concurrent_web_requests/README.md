# Chapter 4: Concurrent web requests: gather, as_completed, wait

Run: `uv run python -m workshop.ch04_concurrent_web_requests.<file>`

| File | Listing | Use case |
|---|---|---|
| `01_async_context_manager.py` | 4.1 | Write `__aenter__` / `__aexit__` for resources that need I/O |
| `02_aiohttp_single_request.py` | 4.2 | Non-blocking HTTP with one reused `ClientSession` |
| `03_aiohttp_timeouts.py` | 4.3 | Session-wide and per-request timeouts |
| `04_create_task_in_comprehension_pitfall.py` | 4.4 | **Pitfall:** `await` inside a comprehension runs tasks sequentially |
| `05_create_tasks_then_await.py` | 4.5 | Create all the tasks first, then await them |
| `06_gather_many_requests.py` | 4.6 | Fan out N requests with `gather` |
| `07_gather_preserves_order.py` | 4.7 | `gather` returns results in the order of its inputs |
| `08_as_completed.py` | 4.8 | Handle results as soon as each one arrives |
| `09_as_completed_timeout.py` | 4.9 | Handle whatever finishes within a deadline (the rest keep running!) |
| `10_gather_exceptions.py` | bonus | Default fail-fast vs `return_exceptions=True` |
| `11_wait_all_completed.py` | 4.10 | `wait()` returns `(done, pending)` Task sets |
| `12_wait_handling_exceptions.py` | 4.11 | Inspect `task.exception()` for each task without raising |
| `13_wait_first_exception.py` | 4.12 | All-or-nothing: stop on the first error and cancel the rest |
| `14_wait_first_completed.py` | 4.13 | The fastest response wins (hedged requests) |
| `15_wait_first_completed_loop.py` | 4.14 | Process results as they arrive while keeping the Task objects |
| `16_wait_timeout.py` | 4.15 | Hard deadline without cancelling or raising |
| `17_wait_cancel_slow_task.py` | 4.16 | Cancel only one specific slow task |
| `fetch.py` | – | Helper `fetch_status(session, url, delay)` |

## Which API for which job

| Need | Use |
|---|---|
| All results, in input order | `gather(*aws)` |
| All results, even when some fail | `gather(*aws, return_exceptions=True)` |
| Results as soon as they're ready | `as_completed(aws)` |
| Fine control over done/pending, cancel on first error | `wait(tasks, return_when=FIRST_EXCEPTION)` |
| First result wins | `wait(tasks, return_when=FIRST_COMPLETED)` |
| Deadline for a group | `wait(tasks, timeout=...)` or `async with asyncio.timeout(...)` |
| Fail together, clean up automatically | `asyncio.TaskGroup` (3.11+) |

## Key takeaways

- Create one `ClientSession` per app, not one per request.
- Always set timeouts on network calls.
- `wait()` needs Tasks, not bare coroutines (bare coroutines raise an error since Python 3.11).
- Timeouts in `as_completed` / `wait` **don't cancel** the slow work. Cancel it yourself.
