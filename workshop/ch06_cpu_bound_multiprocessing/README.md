# Chapter 6: CPU-bound work: multiprocessing, MapReduce, shared memory

Run: `uv run python -m workshop.ch06_cpu_bound_multiprocessing.<file>`
MapReduce examples need data: `uv run python -m workshop.ch06_cpu_bound_multiprocessing.generate_ngrams_data`

| File | Listing | Use case |
|---|---|---|
| `01_parallel_processes.py` | 6.1 | Two CPU-bound jobs in parallel processes |
| `02_process_pool_apply.py` | 6.2 | Reuse worker processes (`Pool.apply`, blocking) |
| `03_process_pool_apply_async.py` | 6.3 | Submit jobs without waiting (`apply_async`) |
| `04_process_pool_executor_map.py` | 6.4 | `ProcessPoolExecutor.map` (the standard executor API) |
| `05_process_pool_with_asyncio.py` | 6.5 | CPU work from asyncio: `loop.run_in_executor(process_pool, ...)` |
| `06_map_reduce_basics.py` | 6.6 | The MapReduce pattern on a toy word count |
| `07_word_count_single_process.py` | 6.7 | Baseline: word frequencies in one process |
| `08_map_reduce_process_pool.py` | 6.8 | Parallel map on all cores, then reduce |
| `09_parallel_reduce.py` | 6.9 | Parallelize the reduce step as well |
| `10_shared_memory_value_array.py` | 6.10 | Share data between processes (`Value`, `Array`) |
| `11_shared_memory_race_condition.py` | 6.11 | **Pitfall:** lost updates from a race condition |
| `12_shared_memory_with_lock.py` | 6.12 | Fix it with `get_lock()` |
| `13_shared_state_in_pool_initializer.py` | 6.13 | Give pool workers shared state through an `initializer` |
| `14_map_reduce_with_progress.py` | 6.14 | Live progress from a shared counter while asyncio waits |
| `15_multiple_event_loops_in_processes.py` | 6.15 | One event loop per process to scale I/O-heavy work (the uvicorn `--workers` model) |
| `count.py`, `map_reduce.py`, `generate_ngrams_data.py` | – | Helpers |

## Key takeaways

- Processes sidestep the GIL, so CPU-bound Python code gets real parallel speedup.
- Always use the `if __name__ == "__main__":` guard.
- Arguments and results are **pickled** between processes. Keep them small, and choose chunk sizes that balance that overhead against idle cores.
- Shared memory is fast but needs locks. Prefer returning results over sharing state.
- `run_in_executor` makes a process pool awaitable, so gather / wait / as_completed all work with it.
