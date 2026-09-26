"""Listing 14.6: interleave two generators by hand, a tiny "scheduler".

Use case: understand the mechanics of an event loop. Generators pause at
`yield`, and a loop that resumes several of them in turn gives concurrency on
one thread.

Run: uv run python -m workshop.ch14_advanced_asyncio.06_generators_interleaved
"""

from collections.abc import Generator


def generator(start: int, end: int):
    for i in range(start, end):
        yield i


one_to_five = generator(1, 5)
five_to_ten = generator(5, 10)


def run_generator_step(gen: Generator[int, None, None]):
    try:
        return gen.send(None)
    except StopIteration as si:
        return si.value


while True:
    one_to_five_result = run_generator_step(one_to_five)
    five_to_ten_result = run_generator_step(five_to_ten)
    print(one_to_five_result)
    print(five_to_ten_result)

    if one_to_five_result is None and five_to_ten_result is None:
        break
