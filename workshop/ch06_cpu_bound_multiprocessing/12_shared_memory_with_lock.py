"""Listing 6.12: fix the race with the lock that comes with Value.

Use case: make read-modify-write atomic across processes. Only one process at
a time may run the critical section. Keep critical sections short, because a
lock turns parallel code back into serial code.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.12_shared_memory_with_lock
"""

from multiprocessing import Process, Value


def increment_value(shared_int):
    with shared_int.get_lock():  # same as acquire() ... release(), but exception-safe
        shared_int.value = shared_int.value + 1


if __name__ == "__main__":
    for _ in range(100):
        integer = Value("i", 0)
        procs = [
            Process(target=increment_value, args=(integer,)),
            Process(target=increment_value, args=(integer,)),
        ]

        [p.start() for p in procs]
        [p.join() for p in procs]
        print(integer.value)
        assert integer.value == 2
