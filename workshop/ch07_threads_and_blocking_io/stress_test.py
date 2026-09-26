"""Listing 7.13: an asyncio HTTP load tester that can be driven from another thread.

The GUI thread calls start() and cancel(). Both hand work over to the asyncio loop
running in a background thread:
  * asyncio.run_coroutine_threadsafe(): submit a coroutine, get a concurrent Future
  * loop.call_soon_threadsafe(): schedule a callback on the loop's thread
"""

import asyncio
from asyncio import AbstractEventLoop
from collections.abc import Callable
from concurrent.futures import Future

from aiohttp import ClientSession


class StressTest:
    def __init__(
        self,
        loop: AbstractEventLoop,
        url: str,
        total_requests: int,
        callback: Callable[[int, int], None],
    ):
        self._completed_requests: int = 0
        self._load_test_future: Future | None = None
        self._loop = loop
        self._url = url
        self._total_requests = total_requests
        self._callback = callback
        self._refresh_rate = max(total_requests // 100, 1)

    def start(self):
        future = asyncio.run_coroutine_threadsafe(self._make_requests(), self._loop)
        self._load_test_future = future

    def cancel(self):
        if self._load_test_future:
            self._loop.call_soon_threadsafe(self._load_test_future.cancel)

    async def _get_url(self, session: ClientSession, url: str):
        try:
            async with session.get(url) as response:
                await response.read()
        except Exception as e:
            print(e)
        # safe without a lock: only the event loop thread touches this counter
        self._completed_requests = self._completed_requests + 1
        if self._completed_requests % self._refresh_rate == 0 or self._completed_requests == self._total_requests:
            self._callback(self._completed_requests, self._total_requests)

    async def _make_requests(self):
        async with ClientSession() as session:
            reqs = [self._get_url(session, self._url) for _ in range(self._total_requests)]
            await asyncio.gather(*reqs)
