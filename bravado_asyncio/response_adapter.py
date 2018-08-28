import asyncio
from typing import Any
from typing import cast
from typing import Dict
from typing import TypeVar

from bravado_core.response import IncomingResponse
from multidict import CIMultiDict

from bravado_asyncio.definitions import AsyncioResponse


T = TypeVar('T')


class AioHTTPResponseAdapter(IncomingResponse):
    """Wraps a aiohttp Response object to provide a bravado-like interface
    to the response innards."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def __call__(self: T, response: AsyncioResponse) -> T:
        self._delegate = response.response
        self._remaining_timeout = response.remaining_timeout
        return self

    @property
    def status_code(self) -> int:
        return self._delegate.status

    @property
    def text(self) -> str:
        future = asyncio.run_coroutine_threadsafe(self._delegate.text(), self._loop)
        return future.result(self._remaining_timeout)

    @property
    def raw_bytes(self) -> bytes:
        future = asyncio.run_coroutine_threadsafe(self._delegate.read(), self._loop)
        return future.result(self._remaining_timeout)

    @property
    def reason(self) -> str:
        return cast(str, self._delegate.reason)  # aiohttp 3.4.0 doesn't annotate this attribute correctly

    @property
    def headers(self) -> CIMultiDict:
        return self._delegate.headers

    def json(self, **_: Any) -> Dict[str, Any]:
        future = asyncio.run_coroutine_threadsafe(self._delegate.json(), self._loop)
        return future.result(self._remaining_timeout)


class AsyncioHTTPResponseAdapter(AioHTTPResponseAdapter):
    """Wraps a aiohttp Response object to provide a bravado-like interface to the response innards.
    Methods are coroutines if they call coroutines themselves and need to be awaited."""

    @property
    async def text(self) -> str:  # type: ignore
        return await asyncio.wait_for(self._delegate.text(), timeout=self._remaining_timeout, loop=self._loop)

    @property
    async def raw_bytes(self) -> bytes:  # type: ignore
        return await asyncio.wait_for(self._delegate.read(), timeout=self._remaining_timeout, loop=self._loop)

    async def json(self, **_: Any) -> Dict[str, Any]:  # type: ignore
        return await asyncio.wait_for(self._delegate.json(), timeout=self._remaining_timeout, loop=self._loop)
