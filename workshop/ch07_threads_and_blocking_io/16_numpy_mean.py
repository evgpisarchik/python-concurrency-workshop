"""Listing 7.18: the mean of each row of a large numpy matrix (the baseline).

Use case: the baseline for 17. The book uses 4 billion points (32 GB of RAM),
here we use 100 million (~800 MB). Raise DATA_POINTS if you have the memory.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.16_numpy_mean
"""

import time

import numpy as np

DATA_POINTS = 100_000_000
rows = 50
columns = DATA_POINTS // rows

matrix = np.arange(DATA_POINTS).reshape(rows, columns)

start = time.perf_counter()
res = np.mean(matrix, axis=1)
print(f"{time.perf_counter() - start:.4f} seconds")
