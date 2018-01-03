import pytest

from bravado_asyncio.http_client import AsyncioClient


@pytest.mark.parametrize('params', [
    {'key': ['list', 'of', 'values']},
    {'key': ['value']},
])
def test_prepare_params(params):
    client = AsyncioClient()
    prepared = client.prepare_params(params)
    assert prepared.getall('key') == params['key']
