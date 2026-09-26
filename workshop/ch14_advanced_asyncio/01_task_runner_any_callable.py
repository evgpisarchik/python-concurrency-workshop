"""Listing 14.1: an API that accepts plain functions, coroutine functions AND coroutines.

Use case: library design. Let users register either sync or async
callbacks (hooks, plugins, event handlers) and run each one the right way.

Run: uv run python -m workshop.ch14_advanced_asyncio.01_task_runner_any_callable
"""

import asyncio
import inspect


class TaskRunner:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.tasks = []

    def add_task(self, func):
        self.tasks.append(func)

    async def _run_all(self):
        awaitable_tasks = []

        for task in self.tasks:
            if inspect.iscoroutinefunction(task):  # async def function: call it, then schedule
                awaitable_tasks.append(asyncio.create_task(task()))
            elif inspect.iscoroutine(task):  # already a coroutine object: schedule it
                awaitable_tasks.append(asyncio.create_task(task))
            else:  # plain function: run it on the loop as a callback
                self.loop.call_soon(task)

        await asyncio.gather(*awaitable_tasks)

    def run(self):
        self.loop.run_until_complete(self._run_all())
        self.loop.close()


if __name__ == "__main__":

    def regular_function():
        print("Hello from a regular function!")

    async def coroutine_function():
        print("Running coroutine, sleeping!")
        await asyncio.sleep(1)
        print("Finished sleeping!")

    runner = TaskRunner()
    runner.add_task(coroutine_function)
    runner.add_task(coroutine_function())
    runner.add_task(regular_function)

    runner.run()
