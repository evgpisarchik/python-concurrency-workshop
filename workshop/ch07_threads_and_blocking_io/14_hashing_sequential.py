"""Listing 7.16: hash 10,000 passwords with scrypt, one after another.

Use case: the baseline for 15. scrypt is CPU-bound, BUT hashlib releases
the GIL while hashing.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.14_hashing_sequential
"""

import hashlib
import os
import random
import string
import time


def random_password(length: int) -> bytes:
    ascii_lowercase = string.ascii_lowercase.encode()
    return bytes(random.choice(ascii_lowercase) for _ in range(length))


passwords = [random_password(10) for _ in range(10_000)]


def hash(password: bytes) -> str:
    salt = os.urandom(16)
    return str(hashlib.scrypt(password, salt=salt, n=2048, p=1, r=8))


start = time.perf_counter()

for password in passwords:
    hash(password)

print(f"{time.perf_counter() - start:.4f} seconds")
