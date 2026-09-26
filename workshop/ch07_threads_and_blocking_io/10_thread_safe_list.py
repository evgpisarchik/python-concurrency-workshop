"""Listing 7.10: a thread-safe list wrapper.

Use case: wrap a shared data structure so every public method holds a lock.
find_and_replace calls indices_of while it already holds the lock, so this
MUST be an RLock (with a plain Lock it deadlocks, as in 09).

Run: uv run python -m workshop.ch07_threads_and_blocking_io.10_thread_safe_list
"""

from threading import RLock


class IntListThreadsafe:
    def __init__(self, wrapped_list: list[int]):
        self._lock = RLock()
        self._inner_list = wrapped_list

    def indices_of(self, to_find: int) -> list[int]:
        with self._lock:
            enumerator = enumerate(self._inner_list)
            return [index for index, value in enumerator if value == to_find]

    def find_and_replace(self, to_replace: int, replace_with: int) -> None:
        with self._lock:
            indices = self.indices_of(to_replace)  # re-acquires the lock we already hold
            for index in indices:
                self._inner_list[index] = replace_with


threadsafe_list = IntListThreadsafe([1, 2, 1, 2, 1])
threadsafe_list.find_and_replace(1, 2)
print(threadsafe_list._inner_list)
