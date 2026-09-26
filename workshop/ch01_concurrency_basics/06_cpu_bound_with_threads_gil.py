"""Listing 1.6: CPU-bound work in threads. The GIL means this is NOT faster.

Use case: see the Global Interpreter Lock (GIL) in action. Only one thread
runs Python bytecode at a time, so two CPU-bound threads take about as long
as running them one after another (sometimes longer, because of switching).

Try it: on a free-threaded build (`uv run --python 3.14t ...`) the GIL is
gone and this version runs about 2x faster.

Run: uv run python -m workshop.ch01_concurrency_basics.06_cpu_bound_with_threads_gil
"""

import threading
import time

from workshop.ch01_concurrency_basics.fib import print_fib


def fibs_with_threads():
    first = threading.Thread(target=print_fib, args=(35,))
    second = threading.Thread(target=print_fib, args=(36,))

    first.start()
    second.start()

    first.join()
    second.join()


start = time.perf_counter()
fibs_with_threads()
print(f"Threads took {time.perf_counter() - start:.4f} seconds.")
