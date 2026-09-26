"""Listing 7.9: a recursive function under a Lock deadlocks, and RLock fixes it.

Use case: a function that takes a lock and calls itself (or another method
that takes the same lock). A plain Lock blocks on the second acquire. A
reentrant lock (RLock) lets the thread that owns it acquire it again.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.09_reentrant_lock
"""

from threading import Lock, RLock, Thread


def make_sum_list(list_lock):
    def sum_list(int_list: list[int]) -> int:
        print("Waiting to acquire lock...")
        with list_lock:
            print("Acquired lock.")
            if len(int_list) == 0:
                print("Finished summing.")
                return 0
            head, *tail = int_list
            print("Summing rest of list.")
            return head + sum_list(tail)

    return sum_list


print("--- with Lock (deadlocks on the second acquire) ---")
thread = Thread(target=make_sum_list(Lock()), args=([1, 2, 3, 4],), daemon=True)
thread.start()
thread.join(timeout=2)
print(f"Thread still stuck: {thread.is_alive()}")

print("--- with RLock ---")
thread = Thread(target=make_sum_list(RLock()), args=([1, 2, 3, 4],))
thread.start()
thread.join()
