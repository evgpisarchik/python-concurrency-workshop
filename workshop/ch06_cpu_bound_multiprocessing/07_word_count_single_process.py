"""Listing 6.7: count word frequencies in one process (the baseline).

Use case: the baseline to beat with 08 and 09.

Prereq: uv run python -m workshop.ch06_cpu_bound_multiprocessing.generate_ngrams_data
Run:    uv run python -m workshop.ch06_cpu_bound_multiprocessing.07_word_count_single_process
"""

import time

from workshop.ch06_cpu_bound_multiprocessing.map_reduce import read_ngrams

freqs = {}
lines = read_ngrams()

start = time.perf_counter()

for line in lines:
    data = line.split("\t")
    word = data[0]
    count = int(data[2])
    if word in freqs:
        freqs[word] = freqs[word] + count
    else:
        freqs[word] = count

print(f"Aardvark has appeared {freqs['Aardvark']} times.")
print(f"Single process took {time.perf_counter() - start:.4f} seconds")
