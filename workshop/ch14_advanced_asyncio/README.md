# Chapter 14: Advanced asyncio: API design, contextvars, uvloop, building an event loop

Run: `uv run python -m workshop.ch14_advanced_asyncio.<file>`

| File | Listing | Use case |
|---|---|---|
| `01_task_runner_any_callable.py` | 14.1 | API that accepts sync functions, coroutine functions and coroutines |
| `02_context_variables.py` | 14.2 | Per-task / per-request state with `contextvars` |
| `03_sleep_zero_yield.py` | 14.3 | `await asyncio.sleep(0)` yields to the loop once |
| `04_uvloop.py` | 14.4 | A faster event loop (`uvloop.run`) |
| `05_generator_based_coroutines_legacy.py` | 14.5 | Legacy `yield from` coroutines (`@asyncio.coroutine` was removed in 3.11) |
| `06_generators_interleaved.py` | 14.6 | Hand-rolled scheduler with generators |
| `07_coroutine_send.py` | 14.7 | Drive a coroutine with `.send(None)` |
| `custom_future.py` | 14.8 | A Future in ~25 lines |
| `08_custom_future_manual_loop.py` | 14.9 | What `await future` does, step by step |
| `09_selector_driven_coroutine.py` | 14.10 | Resume a coroutine when the selector says a socket is ready |
| `custom_task.py` | 14.11 | A Task in ~25 lines |
| `custom_event_loop.py` | 14.12 | An event loop in ~70 lines |
| `10_custom_event_loop_server.py` | 14.13 | **A multi-client server on our own event loop** |
| `11_eager_task_factory_modern.py` | bonus | Eager tasks (3.12+) skip scheduling when a task never suspends |

## Key takeaways

- A coroutine is a generator underneath. `await` yields Futures up to whoever is driving it.
- An event loop is: run ready tasks, `select()` on sockets, fire callbacks that resolve futures, repeat.
- `contextvars` is the async-safe replacement for thread-locals.
