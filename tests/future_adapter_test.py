import asyncio
import concurrent.futures

import mock
import pytest

from bravado_asyncio.definitions import AsyncioResponse
from bravado_asyncio.future_adapter import AsyncioFutureAdapter
from bravado_asyncio.future_adapter import FutureAdapter


@pytest.fixture
def mock_future():
    return mock.Mock(name='future')


@pytest.fixture
def mock_response():
    return mock.Mock(name='response')


@pytest.fixture
def mock_wait_for():
    with mock.patch('bravado_asyncio.future_adapter.asyncio.wait_for') as _mock:
        yield _mock


def test_future_adapter(mock_future, mock_response):
    mock_future.result.return_value = mock_response

    future_adapter = FutureAdapter(mock_future)
    result = future_adapter.result(timeout=5)

    assert isinstance(result, AsyncioResponse)
    assert result.response is mock_response
    assert 0 < result.remaining_timeout < 5

    mock_future.result.assert_called_once_with(5)


def test_future_adapter_timeout_error_class():
    """Let's make sure refactors never break timeout errors"""
    assert concurrent.futures.TimeoutError in AsyncioFutureAdapter.timeout_errors


def test_asyncio_future_adapter(mock_future, mock_wait_for, mock_response, event_loop):
    mock_wait_for.return_value = asyncio.coroutine(lambda: mock_response)()

    future_adapter = AsyncioFutureAdapter(mock_future)
    result = event_loop.run_until_complete(future_adapter.result(timeout=5))

    assert isinstance(result, AsyncioResponse)
    assert result.response is mock_response
    assert 0 < result.remaining_timeout < 5

    mock_wait_for.assert_called_once_with(mock_future, timeout=5, loop=None)


def test_asyncio_future_adapter_timeout_error_class():
    """Let's make sure refactors never break timeout errors"""
    assert asyncio.TimeoutError in AsyncioFutureAdapter.timeout_errors
