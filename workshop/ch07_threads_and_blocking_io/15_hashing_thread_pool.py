"""Listing 7.17: the same hashing in a thread pool, which is much faster.

Use case: CPU-bound work in C extensions that release the GIL (hashlib,
zlib, numpy, many image libraries) DOES run in parallel on threads, with no
process start-up or pickling cost.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.15_hashing_thread_pool
"""

import asyncio
import functools
import hashlib
import os
import random
import string
from concurrent.futures import ThreadPoolExecutor

from workshop.common import async_timed


def random_password(length: int) -> bytes:
    ascii_lowercase = string.ascii_lowercase.encode()
    return bytes(random.choice(ascii_lowercase) for _ in range(length))


passwords = [random_password(10) for _ in range(10_000)]


def hash(password: bytes) -> str:
    salt = os.urandom(16)
    return str(hashlib.scrypt(password, salt=salt, n=2048, p=1, r=8))


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    tasks = []

    with ThreadPoolExecutor() as pool:
        for password in passwords:
            tasks.append(loop.run_in_executor(pool, functools.partial(hash, password)))

    await asyncio.gather(*tasks)


asyncio.run(main())
