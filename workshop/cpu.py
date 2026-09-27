"""CPU-bound functions used with threads and process pools.

They live in a module (not in a notebook cell) because process pools pickle a
function by its module and name, and the child process must be able to import it.
"""

import hashlib
import os


def fib(n: int) -> int:
    """Deliberately slow recursive Fibonacci."""
    if n <= 2:
        return n - 1
    return fib(n - 1) + fib(n - 2)


def count(count_to: int) -> int:
    counter = 0
    while counter < count_to:
        counter = counter + 1
    return counter


def hash_password(password: bytes) -> bytes:
    """scrypt is CPU-heavy, but hashlib releases the GIL while it runs."""
    return hashlib.scrypt(password, salt=os.urandom(16), n=2048, p=1, r=8)
