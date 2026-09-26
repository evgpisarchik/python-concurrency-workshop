"""Listing 2.2: calling a coroutine does NOT run it.

Use case: understand the most common beginner bug. Calling a coroutine function
only creates a coroutine object. Nothing runs until an event loop drives it.
Python warns "coroutine ... was never awaited".

Run: uv run python -m workshop.ch02_asyncio_basics.02_coroutine_vs_function
"""


async def coroutine_add_one(number: int) -> int:
    return number + 1


def add_one(number: int) -> int:
    return number + 1


function_result = add_one(1)
coroutine_result = coroutine_add_one(1)

print(f"Function result is {function_result} and the type is {type(function_result)}")
print(f"Coroutine result is {coroutine_result} and the type is {type(coroutine_result)}")
