"""MapReduce helpers for chapter 6 (listings 6.6 and 6.8).

The input is the Google Books Ngram format: one line per (word, year) with
tab-separated fields:  word \t year \t match_count \t volume_count
"""

from collections.abc import Iterator

from workshop.common import DATA_DIR

NGRAMS_FILE = DATA_DIR / "googlebooks-eng-all-1gram-20120701-a"


def partition(data: list, chunk_size: int) -> Iterator[list]:
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def map_frequencies(chunk: list[str]) -> dict[str, int]:
    counter = {}
    for line in chunk:
        word, _, count, _ = line.split("\t")
        if counter.get(word):
            counter[word] = counter[word] + int(count)
        else:
            counter[word] = int(count)
    return counter


def merge_dictionaries(first: dict[str, int], second: dict[str, int]) -> dict[str, int]:
    merged = first
    for key in second:
        if key in merged:
            merged[key] = merged[key] + second[key]
        else:
            merged[key] = second[key]
    return merged


def read_ngrams() -> list[str]:
    if not NGRAMS_FILE.exists():
        raise SystemExit(
            f"{NGRAMS_FILE} not found.\n"
            "Generate a synthetic one:  uv run python -m workshop.ch06_cpu_bound_multiprocessing.generate_ngrams_data\n"
            "or download the real file from http://storage.googleapis.com/books/ngrams/books/datasetsv2.html"
        )
    with open(NGRAMS_FILE, encoding="utf-8") as f:
        return f.readlines()
