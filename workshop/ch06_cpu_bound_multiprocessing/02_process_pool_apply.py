"""Listing 6.2: a process pool with apply(), which blocks per call.

Use case: reuse a fixed set of worker processes (about one per CPU core)
instead of paying the process start-up cost per job. Note that apply() blocks until
the result is back, so these two calls run one after the other.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.02_process_pool_apply
"""

from multiprocessing import Pool


def say_hello(name: str) -> str:
    return f"Hi there, {name}"


if __name__ == "__main__":
    with Pool() as process_pool:
        hi_jeff = process_pool.apply(say_hello, args=("Jeff",))
        hi_john = process_pool.apply(say_hello, args=("John",))
        print(hi_jeff)
        print(hi_john)
