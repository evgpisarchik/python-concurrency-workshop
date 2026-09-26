"""Bonus (Python 3.12+): eager tasks start running synchronously on creation.

Use case: when many tasks finish without ever suspending (cache hits,
memoized results), eager execution skips the scheduling round-trip. The task
runs right away inside create_task() until its first real `await`.

Run: uv run python -m workshop.ch14_advanced_asyncio.11_eager_task_factory_modern
"""

import asyncio

CACHE = {"a": 1}


async def cached_lookup(key: str) -> int:
    print(f"  lookup({key!r}) started")
    if key in CACHE:
        return CACHE[key]  # completes without suspending
    await asyncio.sleep(0.1)
    return 0


async def demo(label: str):
    print(label)
    task = asyncio.create_task(cached_lookup("a"))
    print(f"  after create_task: done={task.done()}")
    await task


async def main():
    await demo("Default task factory:")
    asyncio.get_running_loop().set_task_factory(asyncio.eager_task_factory)
    await demo("Eager task factory:")


asyncio.run(main())
