import asyncio
import io
import os.path
import time
from asyncio import run_coroutine_threadsafe
from concurrent.futures import CancelledError

import pytest
from bravado import requests_client
from bravado.client import SwaggerClient
from bravado.exception import BravadoTimeoutError
from bravado.exception import HTTPBadRequest
from bravado.exception import HTTPInternalServerError
from bravado.exception import HTTPNotFound
from bravado_core.model import Model

from bravado_asyncio import http_client
from bravado_asyncio import thread_loop


@pytest.fixture(scope='module', params=[http_client.AsyncioClient, requests_client.RequestsClient])
def swagger_client(integration_server, request):
    # Run all integration tests twice, once with our AsyncioClient and once again with the RequestsClient
    # to make sure they both behave the same.
    # Once this integration suite has become stable (i.e. we're happy with the approach and the test coverage)
    # it could move to bravado and test all major HTTP clients (requests, fido, asyncio).
    return get_swagger_client(integration_server, request.param())


def get_swagger_client(server_url, http_client_instance):
    spec_url = '{}/swagger.yaml'.format(server_url)
    return SwaggerClient.from_url(
        spec_url,
        http_client=http_client_instance,
        config={'also_return_response': True},
    )


def test_get_query_args(swagger_client):
    response = swagger_client.user.loginUser(
        username='asyncio',
        password='p%s&wörd?',
        invalidate_sessions=True,
    ).response(timeout=1)

    assert response.result == 'success'
    # let's make sure we can access the headers through the response object
    assert response.metadata.headers['X-Rate-Limit'] == '4711'
    assert response.metadata.headers['X-Expires-After'] == 'Expiration date'


def test_param_multi(swagger_client):
    result = swagger_client.pet.getPetsByIds(
        petIds=[23, 42],
    ).response(timeout=1).result

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
    metadata = swagger_client.pet.getPetById(petId=42).response(timeout=1).metadata
    assert metadata.headers['content-type'] == metadata.headers['Content-Type'] == 'application/json; charset=utf-8'


def test_post_form_data(swagger_client):
    result = swagger_client.pet.updatePetWithForm(
        petId=12,
        name='Vivi',
        status='sold',
        userId=42,
        photoUrls=('http://first.url?param1=value1&param2=ß%$', 'http://second.url'),
    ).response(timeout=1).result
    assert result is None


def test_put_json_body(swagger_client):
    # the test server would raise a 404 if the data didn't match
    result = swagger_client.pet.updatePet(
        body={
            'id': 42,
            'category': {
                'name': 'extracute',
            },
            'name': 'Lili',
            'photoUrls': [],
            'status': 'sold',
        },
    ).response(timeout=1).result

    assert result is None


def test_delete_query_args(swagger_client):
    result = swagger_client.pet.deletePet(petId=5).response(timeout=1).result
    assert result is None


def test_post_file_upload(swagger_client):
    with open(os.path.join(os.path.dirname(__file__), '../../testing/sample.jpg'), 'rb') as image:
        result = swagger_client.pet.uploadFile(
            petId=42,
            file=image,
            userId=12,
        ).response(timeout=1).result

    assert result is None


def test_post_file_upload_stream_no_name(swagger_client):
    with open(os.path.join(os.path.dirname(__file__), '../../testing/sample.jpg'), 'rb') as image:
        bytes_io = io.BytesIO(image.read())  # BytesIO has no attribute 'name'
        result = swagger_client.pet.uploadFile(
            petId=42,
            file=bytes_io,
            userId=12,
        ).response(timeout=1).result

    assert result is None


def test_multiple_requests(swagger_client):
    fut1 = swagger_client.store.getInventory()
    fut2 = swagger_client.pet.deletePet(petId=5)

    assert fut1.response().result == {}
    assert fut2.response().result is None


def test_get_msgpack(swagger_client):
    response = swagger_client.pet.getPetsByName(petName='lili').response(timeout=1)

    assert len(response.result) == 1
    assert response.result[0]._as_dict() == {
        'id': 42,
        'name': 'Lili',
        'photoUrls': [],
        'category': None,
        'status': None,
        'tags': None,
    }
    assert response.metadata.headers['Content-Type'] == 'application/msgpack'


def test_server_400(swagger_client):
    with pytest.raises(HTTPBadRequest):
        swagger_client.user.loginUser(username='not', password='correct').response(timeout=1)


def test_server_404(swagger_client):
    with pytest.raises(HTTPNotFound):
        swagger_client.pet.getPetById(petId=5).response(timeout=1)


def test_server_500(swagger_client):
    with pytest.raises(HTTPInternalServerError):
        swagger_client.pet.deletePet(petId=42).response(timeout=1)


def test_cancellation(integration_server):
    swagger_client = get_swagger_client(integration_server, http_client.AsyncioClient())
    bravado_future = swagger_client.store.getInventory()  # request takes roughly 1 second to complete
    bravado_future.cancel()

    with pytest.raises(CancelledError):
        bravado_future.result()

    bravado_future.cancel()  # make sure we can call it again without issues


@pytest.mark.xfail(reason='Setting the timeout through aiohttp does not seem to have an effect sometimes')
def test_timeout_request_options(swagger_client):
    other_future = swagger_client.pet.getPetById(petId=42)
    with pytest.raises(BravadoTimeoutError):
        bravado_future = swagger_client.store.getInventory(_request_options={'timeout': 0.1})
        bravado_future.response(timeout=None)

    # make sure the exception doesn't disrupt the other request
    assert isinstance(other_future.response(timeout=1).result, Model)


def test_timeout_on_future(swagger_client):
    other_future = swagger_client.pet.getPetById(petId=42)
    with pytest.raises(BravadoTimeoutError):
        bravado_future = swagger_client.store.getInventory()
        bravado_future.response(timeout=0.1)

    # make sure the exception doesn't disrupt the other request
    assert isinstance(other_future.response(timeout=1).result, Model)


@pytest.mark.xfail(reason='Execution time is not always below 2 seconds especially for Python 3.5')
def test_client_from_asyncio(integration_server):
    """Let's make sure that the event loop for our HTTP client that runs in a different thread
    behaves properly with the 'standard' asyncio loop that people would normally use when doing
    asynchronous programming. While we're at it, let's also make sure two instances of
    AsyncioClient work well together."""
    # recreate the separate event loop and client session for the HTTP client so we start with a clean slate
    # this is important since we measure the time this test takes, and the test_timeout() tasks might
    # interfere with it
    loop = thread_loop.get_thread_loop()
    if http_client.client_session:
        run_coroutine_threadsafe(http_client.client_session.close(), loop)
    http_client.client_session = None
    # not going to properly shut down the running loop, this will be cleaned up on exit
    thread_loop.event_loop = None

    # get a second event loop running in the current thread; we'll use this one to run the test
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


async def _test_asyncio_client(integration_server):
    # schedule our first coroutine (after _test_asyncio_client) in the default event loop
    future = asyncio.ensure_future(sleep_coroutine())
    client1 = get_swagger_client(integration_server, http_client.AsyncioClient())
    client2 = get_swagger_client(integration_server.replace('localhost', '127.0.0.1'), http_client.AsyncioClient())

    # two tasks for the event loop running in a separate thread
    future1 = client1.store.getInventory()
    future2 = client2.store.getInventory()

    result = await future
    assert result == 42

    result1 = future1.response(timeout=5).result
    assert result1 == {}

    result2 = future2.response(timeout=5).result
    assert result2 == {}

    return True
