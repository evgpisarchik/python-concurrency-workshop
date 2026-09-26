"""Generate a synthetic Google Books 1-gram file for the MapReduce examples.

The real 'googlebooks-eng-all-1gram-20120701-a' is ~1.8 GB. This writes a file in
the same format (default 5 million lines, ~100 MB) into ./data/.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.generate_ngrams_data [lines]
"""

import random
import sys

from workshop.ch05_async_databases.products_db import load_common_words
from workshop.ch06_cpu_bound_multiprocessing.map_reduce import NGRAMS_FILE


def main(lines: int) -> None:
    words = [w.capitalize() for w in load_common_words()] + ["Aardvark"]
    NGRAMS_FILE.parent.mkdir(exist_ok=True)
    with open(NGRAMS_FILE, "w", encoding="utf-8") as f:
        for _ in range(lines):
            word = random.choice(words)
            year = random.randint(1800, 2008)
            f.write(f"{word}\t{year}\t{random.randint(1, 500)}\t{random.randint(1, 50)}\n")
    print(f"Wrote {lines:,} lines to {NGRAMS_FILE}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5_000_000)
