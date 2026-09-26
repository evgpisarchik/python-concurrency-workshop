"""Listing 2.21: create and close an event loop by hand.

Use case: code that must control the loop's lifecycle itself (older frameworks,
custom shutdown logic as in chapter 3). Unlike asyncio.run, run_until_complete
does not cancel leftover tasks, so you must clean up.

Run: uv run python -m workshop.ch02_asyncio_basics.19_manual_event_loop
"""

import asyncio


async def main():
    await asyncio.sleep(1)
    print("done")


loop = asyncio.new_event_loop()

try:
    loop.run_until_complete(main())
finally:
    loop.close()
