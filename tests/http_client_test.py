import asyncio

import mock
import pytest
from bravado.http_future import HttpFuture

from bravado_asyncio.future_adapter import FutureAdapter
from bravado_asyncio.http_client import AsyncioClient
from bravado_asyncio.http_client import RunMode
from bravado_asyncio.response_adapter import AioHTTPResponseAdapter


@pytest.fixture
def mock_client_session():
    with mock.patch('aiohttp.ClientSession') as _mock:
        yield _mock


@pytest.fixture(params=RunMode)
def asyncio_client(request, mock_client_session):
    client = AsyncioClient(run_mode=request.param, loop=mock.Mock(spec=asyncio.AbstractEventLoop))
    client.run_coroutine_func = mock.Mock('run_coroutine_func')
    return client


@pytest.fixture
def mock_log():
    with mock.patch('bravado_asyncio.http_client.log') as _mock:
        yield _mock


@pytest.fixture
def request_params():
    return {
        'method': 'GET',
        'url': 'http://swagger.py/client-test',
        'headers': {},
    }


def test_fail_on_unknown_run_mode():
    with pytest.raises(ValueError):
        AsyncioClient(run_mode='unknown/invalid')


def test_request(asyncio_client, mock_client_session, request_params):
    """Make sure request calls the right functions and instantiates the HttpFuture correctly."""
    asyncio_client.response_adapter = mock.Mock(name='response_adapter', spec=AioHTTPResponseAdapter)
    asyncio_client.bravado_future_class = mock.Mock(name='future_class', spec=HttpFuture)
    asyncio_client.future_adapter = mock.Mock(name='future_adapter', spec=FutureAdapter)

    asyncio_client.request(request_params)

    mock_client_session.assert_called_once_with(loop=asyncio_client.loop)
    mock_client_session.return_value.request.assert_called_once_with(
        method=request_params['method'],
        url=request_params['url'],
        params=None,
        data=mock.ANY,
        headers={},
        timeout=None,
    )
    assert mock_client_session.return_value.request.call_args[1]['data']._fields == []
    asyncio_client.run_coroutine_func.assert_called_once_with(
        mock_client_session.return_value.request.return_value,
        loop=asyncio_client.loop,
    )
    asyncio_client.future_adapter.assert_called_once_with(asyncio_client.run_coroutine_func.return_value)
    asyncio_client.response_adapter.assert_called_once_with(loop=asyncio_client.loop)
    asyncio_client.bravado_future_class.assert_called_once_with(
        asyncio_client.future_adapter.return_value,
        asyncio_client.response_adapter.return_value,
        None,
        None,
        False,
    )


def test_simple_get(asyncio_client, mock_client_session, request_params):
    request_params['params'] = {'foo': 'bar'}

    asyncio_client.request(request_params)

    mock_client_session.return_value.request.assert_called_once_with(
        method=request_params['method'],
        url=request_params['url'],
        params=request_params['params'],
        data=mock.ANY,
        headers={},
        timeout=None,
    )
    assert mock_client_session.return_value.request.call_args[1]['data']._fields == []


def test_int_param(asyncio_client, mock_client_session, request_params):
    request_params['params'] = {'foo': 5}

    asyncio_client.request(request_params)
    assert mock_client_session.return_value.request.call_args[1]['params'] == {'foo': '5'}


@pytest.mark.parametrize(
    'param_name, param_value, expected_param_value',
    (
        ('foo', 'bar', 'bar'),
        ('answer', 42, '42'),
        ('answer', False, 'False'),
        ('answer', None, 'None'),  # do we want this?
    )
)
def test_formdata(asyncio_client, mock_client_session, request_params, param_name, param_value, expected_param_value):
    request_params['data'] = {param_name: param_value}

    asyncio_client.request(request_params)

    mock_client_session.return_value.request.assert_called_once_with(
        method=request_params['method'],
        url=request_params['url'],
        params=None,
        data=mock.ANY,
        headers={},
        timeout=None,
    )

    field_data = mock_client_session.return_value.request.call_args[1]['data']._fields[0]
    assert field_data[0]['name'] == param_name
    assert field_data[2] == expected_param_value


def test_file_data(asyncio_client, mock_client_session, request_params):
    class FileObj:
        name = 'foo'

    request_params['method'] = 'POST'
    request_params['files'] = [('picture', ('filename', FileObj))]

    asyncio_client.request(request_params)

    field_data = mock_client_session.return_value.request.call_args[1]['data']._fields[0]
    assert field_data[0]['name'] == 'picture'
    assert field_data[0]['filename'] == 'filename'
    assert field_data[2] == FileObj


def test_file_data_int_filename(asyncio_client, mock_client_session, request_params):
    class FileObj:
        name = 42
        read = mock.Mock()

    request_params['method'] = 'POST'
    request_params['files'] = [('picture', ('filename', FileObj))]

    asyncio_client.request(request_params)

    field_data = mock_client_session.return_value.request.call_args[1]['data']._fields[0]
    assert field_data[0]['name'] == 'picture'
    assert field_data[0]['filename'] == 'filename'
    assert field_data[2] == FileObj.read.return_value


def test_connect_timeout_logs_warning(asyncio_client, mock_client_session, request_params, mock_log):
    request_params['connect_timeout'] = 0.1

    asyncio_client.request(request_params)

    assert mock_log.warning.call_count == 1
    assert 'connect_timeout' in mock_log.warning.call_args[0][0]
    assert mock_client_session.return_value.request.call_args[1]['timeout'] is None
