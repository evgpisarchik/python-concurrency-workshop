"""Listing 14.11: a minimal Task, a Future that drives a coroutine.

step() starts the coroutine. When it yields a CustomFuture, the task subscribes to
it and resumes the coroutine with the result once the future is done.
"""

from workshop.ch14_advanced_asyncio.custom_future import CustomFuture


class CustomTask(CustomFuture):
    def __init__(self, coro, loop):
        super().__init__()
        self._coro = coro
        self._loop = loop
        self._current_result = None
        self._task_state = None
        loop.register_task(self)

    def step(self):
        try:
            if self._task_state is None:
                self._task_state = self._coro.send(None)
            if isinstance(self._task_state, CustomFuture):
                self._task_state.add_done_callback(self._future_done)
        except StopIteration as si:
            self.set_result(si.value)

    def _future_done(self, result):
        self._current_result = result
        try:
            self._task_state = self._coro.send(self._current_result)
        except StopIteration as si:
            self.set_result(si.value)
