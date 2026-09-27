"""MapReduce word count over a Google Books 1-gram file.

Line format: word \\t year \\t match_count \\t volume_count
"""

import random
import sys
from collections.abc import Iterator
from pathlib import Path

from workshop.common import DATA_DIR

NGRAMS_FILE = DATA_DIR / "googlebooks-eng-all-1gram-20120701-a"
COMMON_WORDS_FILE = Path(__file__).parent / "common" / "common_words.txt"


def partition(data: list, chunk_size: int) -> Iterator[list]:
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def map_frequencies(chunk: list[str]) -> dict[str, int]:
    counter: dict[str, int] = {}
    for line in chunk:
        word, _, count, _ = line.split("\t")
        counter[word] = counter.get(word, 0) + int(count)
    return counter


def merge_dictionaries(first: dict[str, int], second: dict[str, int]) -> dict[str, int]:
    merged = first
    for key in second:
        merged[key] = merged.get(key, 0) + second[key]
    return merged


def generate_ngrams(lines: int = 5_000_000) -> Path:
    """Write a synthetic file in the Google Books format (the real one is ~1.8 GB)."""
    words = [w.capitalize() for w in COMMON_WORDS_FILE.read_text().split()] + ["Aardvark"]
    NGRAMS_FILE.parent.mkdir(exist_ok=True)
    with open(NGRAMS_FILE, "w", encoding="utf-8") as f:
        for _ in range(lines):
            word = random.choice(words)
            f.write(f"{word}\t{random.randint(1800, 2008)}\t{random.randint(1, 500)}\t{random.randint(1, 50)}\n")
    return NGRAMS_FILE


def read_ngrams() -> list[str]:
    if not NGRAMS_FILE.exists():
        generate_ngrams()
    with open(NGRAMS_FILE, encoding="utf-8") as f:
        return f.readlines()


if __name__ == "__main__":
    print(f"Wrote {generate_ngrams(int(sys.argv[1]) if len(sys.argv) > 1 else 5_000_000)}")
