"""Writes ~14 MB to stdout: far more than an OS pipe buffer (~64 KB) holds."""

import sys

for _ in range(1_000_000):
    sys.stdout.buffer.write(b"Hello there!!\n")
sys.stdout.flush()
