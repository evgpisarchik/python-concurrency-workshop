"""Listing 13.4: a child program that writes a lot of output (~14 MB) to stdout."""

import sys

for _ in range(1_000_000):
    sys.stdout.buffer.write(b"Hello there!!\n")

sys.stdout.flush()
