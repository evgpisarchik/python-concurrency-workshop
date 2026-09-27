"""Blocks the event loop for 200 ms in debug mode, so asyncio logs a slow-callback warning (notebook 2)."""

import asyncio
import time


async def main():
    time.sleep(0.2)  # blocks the loop


asyncio.run(main(), debug=True)
