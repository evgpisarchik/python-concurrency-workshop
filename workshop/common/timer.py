"""Listing 2.16: decorator that prints how long a coroutine took.

Wrap a coroutine function with @async_timed() to see when it starts and how long
it runs. Comparing timings of nested coroutines is the fastest way to tell
whether your code actually runs concurrently.
"""

import functools
import time
from collections.abc import Awaitable, Callable
from typing import Any


def async_timed():
    def wrapper(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            print(f"starting {func.__name__} with args {args} {kwargs}")
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                total = time.perf_counter() - start
                print(f"finished {func.__name__} in {total:.4f} second(s)")

        return wrapped

    return wrapper
