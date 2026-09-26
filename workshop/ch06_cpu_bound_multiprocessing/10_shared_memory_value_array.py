"""Listing 6.10: share data between processes with Value and Array.

Use case: processes don't share memory by default. multiprocessing.Value /
Array put a C integer or array in shared memory that every process can see.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.10_shared_memory_value_array
"""

from multiprocessing import Array, Process, Value


def increment_value(shared_int):
    shared_int.value = shared_int.value + 1


def increment_array(shared_array):
    for index, integer in enumerate(shared_array):
        shared_array[index] = integer + 1


if __name__ == "__main__":
    integer = Value("i", 0)
    integer_array = Array("i", [0, 0])

    procs = [
        Process(target=increment_value, args=(integer,)),
        Process(target=increment_array, args=(integer_array,)),
    ]

    [p.start() for p in procs]
    [p.join() for p in procs]

    print(integer.value)
    print(integer_array[:])
