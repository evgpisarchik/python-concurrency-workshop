"""`warnings.catch_warnings()` in one asyncio task, a warning raised in another task meanwhile.

Run with `-X context_aware_warnings=0` (the default on the regular build) and `=1` (the default on the
free-threaded build) to see whether the suppression leaks into the other task.
"""

import asyncio
import sys
import warnings

shown = []
warnings.showwarning = lambda message, *args, **kwargs: shown.append(str(message))
warnings.simplefilter("always")


async def quiet_task():
    with warnings.catch_warnings(action="ignore"):  # meant to silence warnings in this task only
        await asyncio.sleep(0.1)


async def loud_task():
    await asyncio.sleep(0.05)  # runs while quiet_task is inside catch_warnings()
    warnings.warn("important warning from another task", stacklevel=1)


async def main():
    await asyncio.gather(quiet_task(), loud_task())
    print(
        f"context_aware_warnings={sys.flags.context_aware_warnings}: the other task's warning was "
        f"{'shown' if shown else 'SWALLOWED'}"
    )


if __name__ == "__main__":
    asyncio.run(main())
