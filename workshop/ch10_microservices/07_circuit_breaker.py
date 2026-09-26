"""Listing 10.12: the circuit breaker in action.

Use case: stop calling a service that is clearly down, so your own service
stays fast (fail fast instead of waiting for timeouts) and the struggling
service gets time to recover.

Run: uv run python -m workshop.ch10_microservices.07_circuit_breaker
"""

import asyncio

from workshop.ch10_microservices.circuit_breaker import CircuitBreaker


async def main():
    async def slow_callback():
        await asyncio.sleep(2)

    cb = CircuitBreaker(slow_callback, timeout=1.0, time_window=5, max_failures=2, reset_interval=5)

    for _ in range(4):
        try:
            await cb.request()
        except Exception:
            pass

    print("Sleeping for 5 seconds so breaker closes...")
    await asyncio.sleep(5)

    for _ in range(4):
        try:
            await cb.request()
        except Exception:
            pass


asyncio.run(main())
