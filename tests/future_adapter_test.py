import asyncio
import concurrent.futures
import time

import mock
import pytest

from bravado_asyncio.definitions import AsyncioResponse
from bravado_asyncio.future_adapter import AsyncioFutureAdapter
from bravado_asyncio.future_adapter import FutureAdapter


@pytest.fixture
def mock_future():
    return mock.Mock(name="future")


@pytest.fixture
def mock_response():
    return mock.Mock(name="response")


def mock_result_with_sleep(response):
    """Return a function that can be used as side effect for mock_future.result, adding in a delay."""

    def _side_effect(timeout=None):
        time.sleep(0.1)
        return response

    return _side_effect


def test_future_adapter(mock_future, mock_response):
    mock_future.result.side_effect = mock_result_with_sleep(mock_response)

    future_adapter = FutureAdapter(mock_future)
    result = future_adapter.result(timeout=5)

    assert isinstance(result, AsyncioResponse)
    assert result.response is mock_response
    assert 0 < result.remaining_timeout < 5


def test_future_adapter_timeout_error_class():
    """Let's make sure refactors never break timeout errors"""
    assert concurrent.futures.TimeoutError in FutureAdapter.timeout_errors


@pytest.mark.asyncio
async def test_asyncio_future_adapter(mock_response):
    mock_future = mock.AsyncMock(name='mock future', side_effect=mock_result_with_sleep(mock_response))

    future_adapter = AsyncioFutureAdapter(mock_future())
    result = await future_adapter.result(timeout=5)

    assert isinstance(result, AsyncioResponse)
    assert result.response is mock_response
    assert 0 < result.remaining_timeout < 5


def test_asyncio_future_adapter_timeout_error_class():
    """Let's make sure refactors never break timeout errors"""
    assert asyncio.TimeoutError in AsyncioFutureAdapter.timeout_errors
