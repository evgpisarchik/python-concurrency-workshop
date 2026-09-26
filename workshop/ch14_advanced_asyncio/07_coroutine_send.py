"""Listing 14.7: drive a coroutine by hand with .send(None).

Use case: see that a coroutine is a generator-like object. Without an event
loop, send(None) runs it until it finishes (StopIteration) or suspends.

Run: uv run python -m workshop.ch14_advanced_asyncio.07_coroutine_send
"""


async def say_hello():
    print("Hello!")


async def say_goodbye():
    print("Goodbye!")


async def meet_and_greet():
    await say_hello()
    await say_goodbye()


coro = meet_and_greet()

try:
    coro.send(None)
except StopIteration:
    print("Coroutine finished (raised StopIteration)")
