"""Listing 10.9: retry a coroutine with a per-attempt timeout.

`coro` is a *factory* (a callable returning a new coroutine) because a coroutine
object can only be awaited once, so every attempt needs a fresh one.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable


class TooManyRetries(Exception):
    pass


async def retry(coro: Callable[[], Awaitable], max_retries: int, timeout: float, retry_interval: float):
    for retry_num in range(0, max_retries):
        try:
            return await asyncio.wait_for(coro(), timeout=timeout)
        except Exception as e:
            logging.exception(f"Exception while waiting (tried {retry_num} times), retrying.", exc_info=e)
            await asyncio.sleep(retry_interval)
    raise TooManyRetries()
