"""Listing 14.9: poll a CustomFuture in a loop until it has a value.

Use case: step through what `await future` does. Every send() either yields
(not done) or raises StopIteration carrying the value (done).

Run: uv run python -m workshop.ch14_advanced_asyncio.08_custom_future_manual_loop
"""

from workshop.ch14_advanced_asyncio.custom_future import CustomFuture

future = CustomFuture()

i = 0

while True:
    try:
        print("Checking future...")
        gen = future.__await__()
        gen.send(None)
        print("Future is not done...")
        if i == 1:
            print("Setting future value...")
            future.set_result("Finished!")
        i = i + 1
    except StopIteration as si:
        print(f"Value is: {si.value}")
        break
