"""Listing 2.6: a coroutine that sleeps, used everywhere as a stand-in for slow I/O."""

import asyncio


async def delay(delay_seconds: float) -> float:
    print(f"sleeping for {delay_seconds} second(s)")
    await asyncio.sleep(delay_seconds)
    print(f"finished sleeping for {delay_seconds} second(s)")
    return delay_seconds
