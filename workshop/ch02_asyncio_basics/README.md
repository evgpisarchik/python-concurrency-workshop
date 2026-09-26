# Chapter 2: Asyncio basics: coroutines, tasks, futures, pitfalls

Run: `uv run python -m workshop.ch02_asyncio_basics.<file>`

| File | Listing | Use case |
|---|---|---|
| `01_first_coroutine.py` | 2.1 | Define a coroutine with `async def` |
| `02_coroutine_vs_function.py` | 2.2 | Calling a coroutine only creates a coroutine object, and nothing runs yet |
| `03_asyncio_run.py` | 2.3 | `asyncio.run()` as the program entry point |
| `04_await_coroutines.py` | 2.4 | Call a coroutine from another one with `await` |
| `05_await_sleep.py` | 2.5 | `asyncio.sleep` as a stand-in for slow I/O |
| `workshop/common/delay.py` | 2.6 | The `delay()` helper used everywhere |
| `06_sequential_awaits.py` | 2.7 | `await` alone is sequential and gives no concurrency |
| `07_create_task.py` | 2.8 | Schedule a coroutine in the background with `create_task` |
| `08_running_tasks_concurrently.py` | 2.9 | Three 3 s waits take 3 s in total, not 9 s |
| `09_running_code_while_waiting.py` | 2.10 | Do other work while tasks wait |
| `10_cancelling_tasks.py` | 2.11 | Cancel a long task with `task.cancel()` |
| `11_timeout_with_wait_for.py` | 2.12 | Time out with `wait_for` and with `asyncio.timeout()` (3.11+) |
| `12_shield_from_cancellation.py` | 2.13 | Warn on a slow task without cancelling it (`shield`) |
| `13_futures_basics.py` | 2.14 | A Future is a placeholder for a later value |
| `14_awaiting_futures.py` | 2.15 | Await a Future that someone else resolves |
| `workshop/common/timer.py` | 2.16 | The `@async_timed()` decorator |
| `15_timing_coroutines.py` | 2.17 | Prove that tasks overlap by timing them |
| `16_cpu_bound_in_coroutines.py` | 2.18 | **Pitfall:** CPU-bound code gets no speedup from asyncio |
| `17_cpu_bound_blocks_io_tasks.py` | 2.19 | **Pitfall:** CPU work delays every other task |
| `18_blocking_library_in_coroutine.py` | 2.20 | **Pitfall:** `requests` inside `async def` blocks the loop |
| `19_manual_event_loop.py` | 2.21 | Create and close a loop by hand |
| `20_call_soon.py` | 2.22 | Schedule a plain callback on the running loop |
| `21_debug_mode.py` | 2.23 | Debug mode reports slow (blocking) callbacks |
| `22_slow_callback_duration.py` | 2.24 | Tune the slow-callback threshold |
| `23_task_group_modern.py` | bonus | `TaskGroup` + `except*`: structured concurrency (3.11+) |

## Key takeaways

- `async def` creates a coroutine. `await` runs it and suspends the caller until it finishes.
- Concurrency comes from **tasks**: `create_task` schedules work and returns right away.
- Use `wait_for` / `asyncio.timeout` for timeouts, `cancel()` to stop work, and `shield()` to protect work from cancellation.
- `Task` is a subclass of `Future`, and both are *awaitables*.
- Two ways to block the loop by accident: **CPU-bound code** and **blocking libraries**.
  An `async def` with no `await` inside is suspicious. Use debug mode (`-X dev` or `PYTHONASYNCIODEBUG=1`) to find them.
- In new code, prefer `asyncio.TaskGroup` to loose `create_task` calls.

## Try it

- In `08`, replace `create_task` with plain `await delay(3)` three times. How long does it take now?
- Run `18` with `-X dev` and read the warnings.
