import asyncio

import aiohttp
import mock
import pytest

from bravado_asyncio.definitions import AsyncioResponse
from bravado_asyncio.response_adapter import AioHTTPResponseAdapter
from bravado_asyncio.response_adapter import AsyncioHTTPResponseAdapter


@pytest.fixture(params=(AioHTTPResponseAdapter, AsyncioHTTPResponseAdapter))
def response_adapter(request, mock_loop):
    return request.param(mock_loop)


@pytest.fixture
def mock_incoming_response():
    return mock.Mock(name="incoming response", spec=aiohttp.ClientResponse)


@pytest.fixture
def asyncio_response(mock_incoming_response):
    return AsyncioResponse(response=mock_incoming_response, remaining_timeout=5)


@pytest.fixture
def mock_run_coroutine_threadsafe():
    with mock.patch(
        "bravado_asyncio.response_adapter.asyncio.run_coroutine_threadsafe"
    ) as _mock:
        yield _mock


@pytest.fixture
def mock_wait_for_result():
    return mock.Mock(name="mock_wait_for result")


@pytest.fixture
def mock_wait_for(mock_wait_for_result):
    with mock.patch("bravado_asyncio.response_adapter.asyncio.wait_for") as _mock:
        _mock.return_value = asyncio.coroutine(lambda: mock_wait_for_result)()
        yield _mock


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


def test_thread_methods(
    mock_run_coroutine_threadsafe, asyncio_response, mock_incoming_response, mock_loop
):
    response_adapter = AioHTTPResponseAdapter(mock_loop)(asyncio_response)

    assert (
        response_adapter.text
        is mock_run_coroutine_threadsafe.return_value.result.return_value
    )
    mock_run_coroutine_threadsafe.assert_called_once_with(
        mock_incoming_response.text.return_value, mock_loop
    )
    mock_run_coroutine_threadsafe.return_value.result.assert_called_once_with(
        asyncio_response.remaining_timeout
    )

    assert (
        response_adapter.raw_bytes
        is mock_run_coroutine_threadsafe.return_value.result.return_value
    )
    mock_run_coroutine_threadsafe.assert_called_with(
        mock_incoming_response.read.return_value, mock_loop
    )
    mock_run_coroutine_threadsafe.return_value.result.assert_called_with(
        asyncio_response.remaining_timeout
    )

    assert (
        response_adapter.json()
        is mock_run_coroutine_threadsafe.return_value.result.return_value
    )
    mock_run_coroutine_threadsafe.assert_called_with(
        mock_incoming_response.json.return_value, mock_loop
    )
    mock_run_coroutine_threadsafe.return_value.result.assert_called_with(
        asyncio_response.remaining_timeout
    )

    assert mock_run_coroutine_threadsafe.call_count == 3
    assert mock_run_coroutine_threadsafe.return_value.result.call_count == 3


def test_asyncio_text(
    mock_wait_for,
    mock_wait_for_result,
    asyncio_response,
    mock_incoming_response,
    event_loop,
):
    response_adapter = AsyncioHTTPResponseAdapter(event_loop)(asyncio_response)

    result = event_loop.run_until_complete(response_adapter.text)
    assert result is mock_wait_for_result
    mock_wait_for.assert_called_once_with(
        mock_incoming_response.text.return_value,
        timeout=asyncio_response.remaining_timeout,
        loop=event_loop,
    )


def test_asyncio_raw_bytes(
    mock_wait_for,
    mock_wait_for_result,
    asyncio_response,
    mock_incoming_response,
    event_loop,
):
    response_adapter = AsyncioHTTPResponseAdapter(event_loop)(asyncio_response)

    result = event_loop.run_until_complete(response_adapter.raw_bytes)
    assert result is mock_wait_for_result
    mock_wait_for.assert_called_once_with(
        mock_incoming_response.read.return_value,
        timeout=asyncio_response.remaining_timeout,
        loop=event_loop,
    )


def test_asyncio_json(
    mock_wait_for,
    mock_wait_for_result,
    asyncio_response,
    mock_incoming_response,
    event_loop,
):
    response_adapter = AsyncioHTTPResponseAdapter(event_loop)(asyncio_response)

    result = event_loop.run_until_complete(response_adapter.json())
    assert result is mock_wait_for_result
    mock_wait_for.assert_called_once_with(
        mock_incoming_response.json.return_value,
        timeout=asyncio_response.remaining_timeout,
        loop=event_loop,
    )
