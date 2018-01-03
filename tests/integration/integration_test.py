import asyncio
import io
import os.path
import time

import pytest
from bravado import requests_client
from bravado.client import SwaggerClient
from bravado.exception import BravadoTimeoutError
from bravado.exception import HTTPBadRequest
from bravado.exception import HTTPInternalServerError
from bravado.exception import HTTPNotFound

from bravado_asyncio import http_client


@pytest.fixture(params=[http_client.AsyncioClient, requests_client.RequestsClient])
def swagger_client(integration_server, request):
    # Run all integration tests twice, once with our AsyncioClient and once again with the RequestsClient
    # to make sure they both behave the same.
    # Once this integration suite has become stable (i.e. we're happy with the approach and the test coverage)
    # it could move to bravado and test all major HTTP clients (requests, fido, asyncio).
    spec_url = '{}/swagger.yaml'.format(integration_server)
    return SwaggerClient.from_url(
        spec_url,
        http_client=request.param(),
        config={'also_return_response': True},
    )


def test_get_query_args(swagger_client):
    result, response = swagger_client.user.loginUser(
        username='asyncio',
        password='password',
        invalidate_sessions=True,
    ).result(timeout=1)

    assert result == 'success'
    # let's make sure we can access the headers through the response object
    assert response.headers['X-Rate-Limit'] == '4711'
    assert response.headers['X-Expires-After'] == 'Expiration date'


def test_param_multi(swagger_client):
    result, response = swagger_client.pet.getPetsByIds(
        petIds=[23, 42],
    ).result(timeout=1)

    assert len(result) == 2
    assert result[0]._as_dict() == {
        'id': 23,
        'name': 'Takamoto',
        'photoUrls': [],
        'category': None,
        'status': None,
        'tags': None,
    }
    assert result[1]._as_dict() == {
        'id': 42,
        'name': 'Lili',
        'photoUrls': [],
        'category': None,
        'status': None,
        'tags': None,
    }


def test_response_headers(swagger_client):
    """Make sure response headers are returned in the same format across HTTP clients. Namely,
    make sure names and values are str, and that it's possible to access headers in a
    case-insensitive manner."""
    _, response = swagger_client.pet.getPetById(petId=42).result(timeout=1)
    assert response.headers['content-type'] == response.headers['Content-Type'] == 'application/json; charset=utf-8'


def test_post_form_data(swagger_client):
    result, _ = swagger_client.pet.updatePetWithForm(
        petId=12,
        name='Vivi',
        status='sold',
        userId=42,
    ).result(timeout=1)
    assert result is None


def test_put_json_body(swagger_client):
    # the test server would raise a 404 if the data didn't match
    result, _ = swagger_client.pet.updatePet(
        body={
            'id': 42,
            'category': {
                'name': 'extracute',
            },
            'name': 'Lili',
            'photoUrls': [],
            'status': 'sold',
        },
    ).result(timeout=1)

    assert result is None


def test_delete_query_args(swagger_client):
    result, _ = swagger_client.pet.deletePet(petId=5).result(timeout=1)
    assert result is None


def test_post_file_upload(swagger_client):
    with open(os.path.join(os.path.dirname(__file__), '../../testing/sample.jpg'), 'rb') as image:
        result, _ = swagger_client.pet.uploadFile(
            petId=42,
            file=image,
            userId=12,
        ).result(timeout=1)


def test_post_file_upload_stream_no_name(swagger_client):
    with open(os.path.join(os.path.dirname(__file__), '../../testing/sample.jpg'), 'rb') as image:
        bytes_io = io.BytesIO(image.read())  # BytesIO has no attribute 'name'
        result, _ = swagger_client.pet.uploadFile(
            petId=42,
            file=bytes_io,
            userId=12,
        ).result(timeout=1)


def test_get_msgpack(swagger_client):
    result, response = swagger_client.pet.getPetsByName(petName='lili').result(timeout=1)

    assert len(result) == 1
    assert result[0]._as_dict() == {
        'id': 42,
        'name': 'Lili',
        'photoUrls': [],
        'category': None,
        'status': None,
        'tags': None,
    }
    assert response.headers['Content-Type'] == 'application/msgpack'


def test_server_400(swagger_client):
    with pytest.raises(HTTPBadRequest):
        swagger_client.user.loginUser(username='not', password='correct').result(timeout=1)


def test_server_404(swagger_client):
    with pytest.raises(HTTPNotFound):
        swagger_client.pet.getPetById(petId=5).result(timeout=1)


def test_server_500(swagger_client):
    with pytest.raises(HTTPInternalServerError):
        swagger_client.pet.deletePet(petId=42).result(timeout=1)


def test_timeout(swagger_client):
    with pytest.raises(BravadoTimeoutError):
        bravado_future = swagger_client.store.getInventory()
        bravado_future.result(timeout=0.1)


def test_client_from_asyncio(integration_server):
    """Let's make sure that the event loop for our HTTP client that runs in a different thread
    behaves properly with the 'standard' asyncio loop that people would normally use when doing
    asynchronous programming. While we're at it, let's also make sure two instances of
    AsyncioClient work well together."""
    # recreate the separate event loop and client session for the HTTP client so we start with a clean slate
    # this is important since we measure the time this test takes, and the test_timeout() tasks might
    # interfere with it
    http_client.client_session.close()
    http_client.client_session = None
    # not going to properly shut down the running loop, this will be cleaned up on exit
    http_client.loop = None

    loop = asyncio.get_event_loop()
    start_time = time.time()
    loop.run_until_complete(_test_asyncio_client(integration_server))
    end_time = time.time()

    # There are three things being executed asynchronously:
    # 1. sleep 1 second in the main event loop
    # 2. fetch the response for client1 (the server sleeps 1 second)
    # 3. fetch the response for client2 (the server sleeps 1 second)
    # All of this combined should take only a bit more than one second.
    # While this assertion could become flaky depending on how busy the system that runs the test
    # is for now it's a nice confirmation that things work as expected. We can remove it later if
    # it becomes a problem.
    assert end_time - start_time < 2


async def sleep_coroutine():
    await asyncio.sleep(1)
    return 42


async def get_swagger_client(spec_url):
    return SwaggerClient.from_url(
        spec_url,
        http_client=http_client.AsyncioClient(),
    )


async def _test_asyncio_client(integration_server):
    spec_url = '{}/swagger.yaml'.format(integration_server)
    # schedule our first coroutine (after _test_asyncio_client) in the default event loop
    future = asyncio.ensure_future(sleep_coroutine())
    # more work for the default event loop
    client1 = await get_swagger_client(spec_url)
    client2 = await get_swagger_client(spec_url.replace('localhost', '127.0.0.1'))

    # two tasks for the event loop running in a separate thread
    future1 = client1.store.getInventory()
    future2 = client2.store.getInventory()

    result = await future
    assert result == 42

    result1 = future1.result(timeout=5)
    assert result1 == {}

    result2 = future2.result(timeout=5)
    assert result2 == {}

    return True
