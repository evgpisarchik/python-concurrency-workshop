"""Listing 10.10: retry failing and timing-out calls.

Use case: absorb transient failures (network blips, a service restarting)
without failing the user's request. Retry a fixed number of times, then give up.

Run: uv run python -m workshop.ch10_microservices.06_retry
"""

import asyncio

from workshop.ch10_microservices.retry import TooManyRetries, retry


async def main():
    async def always_fail():
        raise Exception("I've failed!")

    async def always_timeout():
        await asyncio.sleep(1)

    try:
        await retry(always_fail, max_retries=3, timeout=0.1, retry_interval=0.1)
    except TooManyRetries:
        print("Retried too many times!")

    try:
        await retry(always_timeout, max_retries=3, timeout=0.1, retry_interval=0.1)
    except TooManyRetries:
        print("Retried too many times!")


asyncio.run(main())
