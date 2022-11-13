import asyncio
import logging
from unittest import mock

import pytest


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.stop()
    loop.close()


@pytest.fixture
def mock_loop():
    return mock.Mock(name="loop")


@pytest.fixture(autouse=True, scope="session")
def set_log_level():
    logging.basicConfig(level=logging.DEBUG)
