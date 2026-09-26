"""Listing 6.11: PITFALL. A race condition on shared memory.

Use case: see that "x = x + 1" is read-modify-write, not atomic. When two
processes interleave, one increment is lost and the result is 1 instead of 2.
It is rare, so we repeat the experiment many times and count the failures.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.11_shared_memory_race_condition
"""

from multiprocessing import Process, Value, cpu_count


def increment_value(shared_int):
    shared_int.value = shared_int.value + 1


if __name__ == "__main__":
    print(f"CPU count: {cpu_count()}")
    failures = 0
    runs = 1000
    for _ in range(runs):
        integer = Value("i", 0)
        procs = [
            Process(target=increment_value, args=(integer,)),
            Process(target=increment_value, args=(integer,)),
        ]

        [p.start() for p in procs]
        [p.join() for p in procs]
        if integer.value != 2:
            failures += 1
            print(f"Race condition! value = {integer.value}")
    print(f"{failures}/{runs} runs lost an update")
