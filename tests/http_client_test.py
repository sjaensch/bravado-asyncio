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


@pytest.fixture
def asyncio_client(mock_client_session, ssl_verify=None, ssl_cert=None):
    client = AsyncioClient(
        run_mode=RunMode.THREAD,
        loop=mock.Mock(spec=asyncio.AbstractEventLoop),
        ssl_verify=ssl_verify,
        ssl_cert=ssl_cert,
    )
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


@pytest.fixture
def mock_aiohttp_version():
    with mock.patch('aiohttp.__version__', new='3.0.0'):
        yield


@pytest.fixture
def mock_create_default_context():
    with mock.patch('ssl.create_default_context', autospec=True) as _mock:
        yield _mock


def test_fail_on_unknown_run_mode():
    with pytest.raises(ValueError):
        AsyncioClient(run_mode='unknown/invalid')


@pytest.mark.usefixtures('mock_aiohttp_version')
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
        skip_auto_headers=['Content-Type'],
        ssl=None,
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
        request_config=None,
    )


@pytest.mark.usefixtures('mock_aiohttp_version')
def test_simple_get(asyncio_client, mock_client_session, request_params):
    request_params['params'] = {'foo': 'bar'}

    asyncio_client.request(request_params)

    mock_client_session.return_value.request.assert_called_once_with(
        method=request_params['method'],
        url=request_params['url'],
        params=request_params['params'],
        data=mock.ANY,
        headers={},
        skip_auto_headers=['Content-Type'],
        ssl=None,
        timeout=None,
    )
    assert mock_client_session.return_value.request.call_args[1]['data']._fields == []


def test_int_param(asyncio_client, mock_client_session, request_params):
    request_params['params'] = {'foo': 5}

    asyncio_client.request(request_params)
    assert mock_client_session.return_value.request.call_args[1]['params'] == {'foo': '5'}


@pytest.mark.usefixtures('mock_aiohttp_version')
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
        skip_auto_headers=['Content-Type'],
        ssl=None,
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


@pytest.mark.usefixtures('mock_aiohttp_version')
def test_disable_ssl_verification(mock_client_session, mock_create_default_context):
    client = asyncio_client(mock_client_session=mock_client_session, ssl_verify=False)
    client.request({})
    assert mock_client_session.return_value.request.call_args[1]['ssl'] is False
    assert mock_create_default_context.call_count == 0


@pytest.mark.usefixtures('mock_aiohttp_version')
def test_use_custom_ssl_ca(mock_client_session, mock_create_default_context):
    client = asyncio_client(mock_client_session=mock_client_session, ssl_verify='my_ca_cert')
    client.request({})
    assert mock_client_session.return_value.request.call_args[1]['ssl'] == mock_create_default_context.return_value
    mock_create_default_context.assert_called_once_with(cafile='my_ca_cert')
    assert mock_create_default_context.return_value.load_cert_chain.call_count == 0


@pytest.mark.usefixtures('mock_aiohttp_version')
@pytest.mark.parametrize(
    'ssl_cert, expected_args',
    (
        ('my_cert', ('my_cert',)),
        (['my_cert'], ('my_cert',)),
        (['my_cert', 'my_key'], ('my_cert', 'my_key')),
    ),
)
def test_use_custom_ssl_cert(ssl_cert, expected_args, mock_client_session, mock_create_default_context):
    client = asyncio_client(mock_client_session=mock_client_session, ssl_cert=ssl_cert)
    client.request({})
    assert mock_client_session.return_value.request.call_args[1]['ssl'] == mock_create_default_context.return_value
    assert mock_create_default_context.return_value.load_cert_chain.call_args[0] == expected_args


@pytest.mark.usefixtures('mock_aiohttp_version')
def test_use_custom_ssl_ca_and_cert(mock_client_session, mock_create_default_context):
    client = asyncio_client(mock_client_session=mock_client_session, ssl_verify='my_ca_cert', ssl_cert='my_cert')
    client.request({})
    assert mock_client_session.return_value.request.call_args[1]['ssl'] == mock_create_default_context.return_value
    mock_create_default_context.assert_called_once_with(cafile='my_ca_cert')
    assert mock_create_default_context.return_value.load_cert_chain.call_args[0] == ('my_cert',)
