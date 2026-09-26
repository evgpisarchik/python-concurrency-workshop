"""Listing 13.7: run 100 subprocesses concurrently.

Use case: parallelize CPU-heavy CLI tools (encryption, compression, image
conversion). Each subprocess is a separate OS process, so this uses all cores
with no GIL involved.

Run: uv run python -m workshop.ch13_subprocesses.06_concurrent_subprocesses   (needs gpg)
"""

import asyncio
import random
import string
import time

from workshop.ch13_subprocesses.gpg import encrypt, require_gpg


async def main():
    require_gpg()
    text_list = ["".join(random.choice(string.ascii_letters) for _ in range(1000)) for _ in range(100)]

    s = time.perf_counter()
    tasks = [asyncio.create_task(encrypt(text)) for text in text_list]
    encrypted_text = await asyncio.gather(*tasks)
    print(f"Total time: {time.perf_counter() - s:.4f}")
    print(f"Encrypted {len(encrypted_text)} texts, first one starts with {encrypted_text[0][:16]!r}")


asyncio.run(main())
