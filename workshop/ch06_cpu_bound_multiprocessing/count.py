"""CPU-bound helper: count to a number in pure Python."""

import time


def count(count_to: int) -> int:
    start = time.perf_counter()
    counter = 0
    while counter < count_to:
        counter = counter + 1
    print(f"Finished counting to {count_to} in {time.perf_counter() - start:.4f}")
    return counter
