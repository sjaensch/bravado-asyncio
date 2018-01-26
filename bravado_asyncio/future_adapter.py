import asyncio
import concurrent.futures
import time
from typing import Optional

from bravado.http_future import FutureAdapter as BaseFutureAdapter

from bravado_asyncio.definitions import AsyncioResponse


class FutureAdapter(BaseFutureAdapter):
    """FutureAdapter that will be used when run_mode is THREAD. The result method is
    a normal Python function, and we expect future to be from the concurrent.futures module."""

    timeout_errors = (concurrent.futures.TimeoutError,)

    def __init__(self, future: concurrent.futures.Future) -> None:
        self.future = future

    def result(self, timeout: Optional[float]=None) -> AsyncioResponse:
        start = time.monotonic()
        response = self.future.result(timeout)
        time_elapsed = time.monotonic() - start
        remaining_timeout = timeout - time_elapsed if timeout else None

        return AsyncioResponse(response=response, remaining_timeout=remaining_timeout)


class AsyncioFutureAdapter(BaseFutureAdapter):
    """FutureAdapter that will be used when run_mode is FULL_ASYNCIO. The result method is
    a coroutine, and we expect future to be awaitable."""

    timeout_errors = (asyncio.TimeoutError,)

    def __init__(self, future: asyncio.Future) -> None:
        self.future = future

    async def result(self, timeout: Optional[float]=None) -> AsyncioResponse:
        start = time.monotonic()
        response = await asyncio.wait_for(self.future, timeout=timeout)
        time_elapsed = time.monotonic() - start
        remaining_timeout = timeout - time_elapsed if timeout else None

        return AsyncioResponse(response=response, remaining_timeout=remaining_timeout)
