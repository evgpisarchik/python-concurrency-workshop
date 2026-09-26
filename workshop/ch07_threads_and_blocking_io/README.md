# Chapter 7: Threads: blocking libraries, locks, GUIs, GIL-releasing work

Run: `uv run python -m workshop.ch07_threads_and_blocking_io.<file>`

| File | Listing | Use case |
|---|---|---|
| `01_threaded_echo_server.py` | 7.1 | Thread per client: concurrency without rewriting blocking code |
| `02_threaded_echo_server_shutdown.py` | 7.2 | Stop threads cleanly (`socket.shutdown` unblocks `recv`) |
| `03_blocking_requests_sequential.py` | 7.3 | Baseline: blocking HTTP |
| `04_thread_pool_executor.py` | 7.4 | `ThreadPoolExecutor.map` for blocking I/O, no asyncio involved |
| `05_thread_pool_with_asyncio.py` | 7.5 | Blocking SDK inside asyncio: `run_in_executor(thread_pool, ...)` |
| `06_default_executor.py` | 7.6 | `run_in_executor(None, ...)`: the loop's default pool |
| `07_asyncio_to_thread.py` | 7.7 | `asyncio.to_thread`, the recommended one-liner |
| `08_thread_lock_progress_counter.py` | 7.8 | Thread-safe counter with `threading.Lock` plus an asyncio progress reporter |
| `09_reentrant_lock.py` | 7.9 | Recursion + `Lock` leads to deadlock. `RLock` fixes it |
| `10_thread_safe_list.py` | 7.10 | Thread-safe wrapper class (with `RLock`) |
| `11_deadlock.py` | 7.11 | Classic deadlock (locks taken in opposite orders) |
| `12_tkinter_hello.py` | 7.12 | A GUI mainloop owns the main thread |
| `stress_test.py` | 7.13 | Thread-safe bridge: `run_coroutine_threadsafe`, `call_soon_threadsafe` |
| `load_tester_gui.py` | 7.14 | Tk UI that polls a `queue.Queue` for updates coming from asyncio |
| `13_load_tester_app.py` | 7.15 | **asyncio loop in a background thread next to a GUI** |
| `14_hashing_sequential.py` | 7.16 | Baseline: scrypt hashing |
| `15_hashing_thread_pool.py` | 7.17 | C extensions that release the GIL give real parallelism with threads |
| `16_numpy_mean.py` | 7.18 | Baseline: numpy row means |
| `17_numpy_mean_threads.py` | 7.19 | numpy + threads for parallel speedup |

## Key takeaways

- Use threads to wrap **blocking I/O libraries** you cannot replace, ideally through `asyncio.to_thread`.
- Threads also parallelize **C code that releases the GIL** (hashlib, zlib, numpy, Pillow...).
- Threads share memory, so protect read-modify-write with locks. Use `RLock` for re-entrant code,
  and acquire multiple locks in one global order to avoid deadlocks.
- Crossing between threads and the event loop: `asyncio.run_coroutine_threadsafe` and `loop.call_soon_threadsafe`.
  Never touch loop objects or GUI widgets from the wrong thread.
