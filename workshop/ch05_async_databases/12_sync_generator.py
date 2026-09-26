"""Listing 5.13: a regular (synchronous) generator.

Use case: a refresher before async generators. `yield` produces values lazily,
one next() at a time.

Run: uv run python -m workshop.ch05_async_databases.12_sync_generator
"""


def positive_integers(until: int):
    for integer in range(until):
        yield integer


positive_iterator = positive_integers(2)

print(next(positive_iterator))
print(next(positive_iterator))
