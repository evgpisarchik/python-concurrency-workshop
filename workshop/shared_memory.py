"""Process workers that share memory through multiprocessing.Value."""

shared_counter = None


def increment_value(shared_int) -> None:
    shared_int.value = shared_int.value + 1  # read-modify-write: NOT atomic


def init_counter(counter) -> None:
    """Pool initializer: runs once in every worker process and stores the shared Value."""
    global shared_counter
    shared_counter = counter


def increment_shared_counter() -> None:
    with shared_counter.get_lock():
        shared_counter.value += 1


def increment_many(shared_int, times: int) -> None:
    for _ in range(times):
        shared_int.value += 1  # read, add, write: another process can write in between


def increment_many_locked(shared_int, times: int) -> None:
    for _ in range(times):
        with shared_int.get_lock():
            shared_int.value += 1
