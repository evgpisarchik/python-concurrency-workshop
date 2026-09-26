"""Listing 13.8: cap concurrent subprocesses with a Semaphore(cpu_count).

Use case: spawning 1000 processes at once thrashes the machine (and can hit
the open file / process limits). Run at most one per core at a time.

Run: uv run python -m workshop.ch13_subprocesses.07_limit_subprocesses_semaphore   (needs gpg)
"""

import asyncio
import os
import random
import string
import time
from asyncio import Semaphore

from workshop.ch13_subprocesses.gpg import encrypt, require_gpg


async def encrypt_limited(sem: Semaphore, text: str) -> bytes:
    async with sem:
        return await encrypt(text)


async def main():
    require_gpg()
    text_list = ["".join(random.choice(string.ascii_letters) for _ in range(1000)) for _ in range(1000)]
    semaphore = Semaphore(os.cpu_count())
    s = time.perf_counter()
    tasks = [asyncio.create_task(encrypt_limited(semaphore, text)) for text in text_list]
    await asyncio.gather(*tasks)
    print(f"Total time: {time.perf_counter() - s:.4f}")


asyncio.run(main())
