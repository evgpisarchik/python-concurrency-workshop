# Chapter 1: Concurrency basics: processes, threads, the GIL

Run any file with `uv run python -m workshop.ch01_concurrency_basics.<file_without_.py>`.

| File | Listing | Use case |
|---|---|---|
| `01_io_vs_cpu_bound.py` | 1.1 | Classify each step of a program as I/O-bound or CPU-bound before choosing a tool |
| `02_processes_and_threads.py` | 1.2 | Inspect the current process id and thread count |
| `03_multithreading.py` | 1.3 | Run a function in a background thread (`start` / `join`) |
| `04_multiprocessing.py` | 1.4 | Run a function in a child process, including the `__main__` guard |
| `05_cpu_bound_sequential.py` | 1.5 | Baseline timing for CPU-bound work |
| `06_cpu_bound_with_threads_gil.py` | 1.6 | See the GIL: threads do not speed up CPU-bound Python code |
| `07_io_bound_sequential.py` | 1.7 | Baseline timing for I/O-bound work |
| `08_io_bound_with_threads.py` | 1.8 | Threads DO speed up I/O-bound work, because the GIL is released while waiting |
| `fib.py` | – | Helper: slow recursive Fibonacci |

## Key takeaways

- **I/O-bound** work waits on the network or disk, and **CPU-bound** work keeps the processor busy.
- A **process** has its own memory and its own GIL. **Threads** share their process's memory.
- The **GIL** allows only one thread at a time to run Python bytecode. Threads still help with I/O
  because blocking system calls release the GIL.
- Asyncio gets I/O concurrency on **one thread**. It uses non-blocking sockets and an **event loop**
  that asks the OS which sockets are ready (chapter 3 builds one).

```
               ┌──────────── event loop (1 thread) ────────────┐
 task A ──run──┤ await socket ─► paused   ...ready! ─► resume   │
 task B ───────┤        run ─► await db ─► paused  ...          │
 task C ───────┤               run ─► done                      │
               └────────────────────────────────────────────────┘
```

## Try it

- Compare 05 and 06. Then run 06 on a free-threaded build: `uv run --python 3.14t python -m ...`.
- Compare 07 and 08. Add a third `read_example()` and see how the totals change.
