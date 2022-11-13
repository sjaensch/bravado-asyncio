import asyncio
from unittest import mock

import aiohttp
import pytest

from bravado_asyncio.definitions import AsyncioResponse
from bravado_asyncio.response_adapter import AioHTTPResponseAdapter
from bravado_asyncio.response_adapter import AsyncioHTTPResponseAdapter
from testing.loop_runner import LoopRunner


@pytest.fixture(params=(AioHTTPResponseAdapter, AsyncioHTTPResponseAdapter))
def response_adapter(request, mock_loop):
    return request.param(mock_loop)


@pytest.fixture
def mock_incoming_response():
    response = mock.Mock(name="incoming response", spec=aiohttp.ClientResponse)
    response.text.return_value = "response text"
    response.read.return_value = b"raw response"
    response.json.return_value = {"json": "response"}
    return response


@pytest.fixture
def asyncio_response(mock_incoming_response):
    return AsyncioResponse(response=mock_incoming_response, remaining_timeout=5)


def test_initialization(response_adapter, mock_loop, asyncio_response):
    called_response_adapter = response_adapter(asyncio_response)

    assert called_response_adapter is response_adapter
    assert response_adapter._loop is mock_loop
    assert response_adapter._delegate is asyncio_response.response
    assert response_adapter._remaining_timeout is asyncio_response.remaining_timeout


def test_properties(response_adapter, asyncio_response, mock_incoming_response):
    response_adapter(asyncio_response)
    assert response_adapter.status_code is mock_incoming_response.status
    assert response_adapter.reason is mock_incoming_response.reason
    assert response_adapter.headers is mock_incoming_response.headers


@pytest.fixture
def loop_runner():
    loop_runner = LoopRunner(asyncio.new_event_loop())
    loop_runner.start()
    yield loop_runner
    loop_runner.stop()
    loop_runner.join()


def test_thread_methods(asyncio_response, loop_runner):
    response_adapter = AioHTTPResponseAdapter(loop_runner.loop)(asyncio_response)

    assert response_adapter.text == "response text"
    assert response_adapter.raw_bytes == b"raw response"
    assert response_adapter.json() == {"json": "response"}


@pytest.mark.asyncio
async def test_asyncio_methods(asyncio_response):
    response_adapter = AsyncioHTTPResponseAdapter(asyncio.get_event_loop())(
        asyncio_response
    )

    result = await response_adapter.text
    assert result == "response text"

    result = await response_adapter.raw_bytes
    assert result == b"raw response"

    result = await response_adapter.json()
    assert result == {"json": "response"}
