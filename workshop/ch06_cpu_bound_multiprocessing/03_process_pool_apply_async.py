"""Listing 6.3: apply_async() submits jobs without waiting.

Use case: submit many jobs at once and collect the results later with .get().
Both jobs now run in parallel. The drawback: .get() blocks, and you have to
choose the order in which to wait.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.03_process_pool_apply_async
"""

from multiprocessing import Pool


def say_hello(name: str) -> str:
    return f"Hi there, {name}"


if __name__ == "__main__":
    with Pool() as process_pool:
        hi_jeff = process_pool.apply_async(say_hello, args=("Jeff",))
        hi_john = process_pool.apply_async(say_hello, args=("John",))
        print(hi_jeff.get())
        print(hi_john.get())
