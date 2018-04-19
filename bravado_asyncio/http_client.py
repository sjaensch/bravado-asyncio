import asyncio
import logging
from collections import Mapping
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Union

import aiohttp
from aiohttp.formdata import FormData
from bravado import http_future  # noqa
from bravado.http_client import HttpClient
from bravado.http_future import HttpFuture
from bravado_core.operation import Operation
from bravado_core.response import IncomingResponse
from bravado_core.schema import is_list_like
from multidict import MultiDict

from bravado_asyncio.definitions import RunMode
from bravado_asyncio.future_adapter import AsyncioFutureAdapter
from bravado_asyncio.future_adapter import FutureAdapter
from bravado_asyncio.response_adapter import AioHTTPResponseAdapter
from bravado_asyncio.response_adapter import AsyncioHTTPResponseAdapter
from bravado_asyncio.thread_loop import get_thread_loop


log = logging.getLogger(__name__)


#: module variable holding the current :class:`aiohttp.ClientSession`, so that we can share it between
#: :class:`AsyncioClient` instances. Use :func:`get_client_session` to retrieve it and create one if none
#: is present.
client_session = None  # type: Optional[aiohttp.ClientSession]


def get_client_session(loop: asyncio.AbstractEventLoop) -> aiohttp.ClientSession:
    """Get a shared ClientSession object that can be reused. If none exists yet it will
    create one using the passed-in loop.

    :param loop: an active (i.e. not closed) asyncio event loop
    :return: a ClientSession instance that can be used to do HTTP requests
    """
    global client_session
    if client_session:
        return client_session
    client_session = aiohttp.ClientSession(loop=loop)
    return client_session


class AsyncioClient(HttpClient):
    """Asynchronous HTTP client using the asyncio event loop. Can either use an event loop
    in a separate thread or operate fully asynchronous within the current thread, using
    async / await.
    """

    def __init__(self, run_mode: RunMode=RunMode.THREAD, loop: Optional[asyncio.AbstractEventLoop]=None) -> None:
        """Instantiate a client using the given run_mode. If you do not pass in an event loop, then
        either a shared loop in a separate thread (THREAD mode) or the default asyncio
        event loop (FULL_ASYNCIO mode) will be used.
        Not passing in an event loop will make sure we share the :py:class:`aiohttp.ClientSession` object
        between AsyncioClient instances.
        """
        self.run_mode = run_mode
        if self.run_mode == RunMode.THREAD:
            self.loop = loop or get_thread_loop()
            self.run_coroutine_func = asyncio.run_coroutine_threadsafe  # type: Callable
            self.response_adapter = AioHTTPResponseAdapter
            self.bravado_future_class = HttpFuture
            self.future_adapter = FutureAdapter  # type: http_future.FutureAdapter
        elif run_mode == RunMode.FULL_ASYNCIO:
            from aiobravado.http_future import HttpFuture as AsyncioHttpFuture

            self.loop = loop or asyncio.get_event_loop()
            self.run_coroutine_func = asyncio.ensure_future
            self.response_adapter = AsyncioHTTPResponseAdapter
            self.bravado_future_class = AsyncioHttpFuture
            self.future_adapter = AsyncioFutureAdapter
        else:
            raise ValueError('Don\'t know how to handle run mode {}'.format(str(run_mode)))

        # don't use the shared client_session if we've been passed an explicit loop argument
        if loop:
            self.client_session = aiohttp.ClientSession(loop=loop)
        else:
            self.client_session = get_client_session(self.loop)

    def request(
            self,
            request_params: Dict[str, Any],
            operation: Optional[Operation]=None,
            response_callbacks: Optional[Callable[[IncomingResponse, Operation], None]]=None,
            also_return_response: bool=False,
    ) -> HttpFuture:
        """Sets up the request params for aiohttp and executes the request in the background.

        :param request_params: request parameters for the http request.
        :param operation: operation that this http request is for. Defaults
            to None - in which case, we're obviously just retrieving a Swagger
            Spec.
        :param response_callbacks: List of callables to post-process the
            incoming response. Expects args incoming_response and operation.
        :param also_return_response: Consult the constructor documentation for
            :class:`bravado.http_future.HttpFuture`.

        :rtype: :class: `bravado_core.http_future.HttpFuture`
        """

        orig_data = request_params.get('data', {})
        if isinstance(orig_data, Mapping):
            data = FormData()
            for name, value in orig_data.items():
                str_value = str(value) if not is_list_like(value) else [str(v) for v in value]
                data.add_field(name, str_value)
        else:
            data = orig_data

        if isinstance(data, FormData):
            for name, file_tuple in request_params.get('files', {}):
                stream_obj = file_tuple[1]
                if not hasattr(stream_obj, 'name') or not isinstance(stream_obj.name, str):
                    # work around an issue in aiohttp: it's not able to deal with names of type int. We've observed
                    # this case in the real world and it is a documented possibility:
                    # https://docs.python.org/3/library/io.html#raw-file-i-o
                    stream_obj = stream_obj.read()

                data.add_field(name, stream_obj, filename=file_tuple[0])

        params = self.prepare_params(request_params.get('params'))

        connect_timeout = request_params.get('connect_timeout')
        if connect_timeout:
            log.warning(
                'bravado-asyncio does not support setting a connect_timeout '
                '(you passed a value of {})'.format(connect_timeout),
            )
        timeout = request_params.get('timeout')

        # aiohttp always adds a Content-Type header, and this breaks some servers that don't
        # expect it for non-POST/PUT requests: https://github.com/aio-libs/aiohttp/issues/457
        skip_auto_headers = ['Content-Type'] if request_params.get('method') not in ['POST', 'PUT'] else None

        coroutine = self.client_session.request(
            method=request_params.get('method') or 'GET',
            url=request_params.get('url'),
            params=params,
            data=data,
            headers=request_params.get('headers'),
            skip_auto_headers=skip_auto_headers,
            timeout=timeout,
        )

        future = self.run_coroutine_func(coroutine, loop=self.loop)

        return self.bravado_future_class(
            self.future_adapter(future),
            self.response_adapter(loop=self.loop),
            operation,
            response_callbacks,
            also_return_response,
        )

    def prepare_params(self, params: Optional[Dict[str, Any]]) -> Union[Optional[Dict[str, Any]], MultiDict]:
        if not params:
            return params

        items = []
        for key, value in params.items():
            entries = [(key, str(value))] if not is_list_like(value) else [(key, str(v)) for v in value]
            items.extend(entries)
        return MultiDict(items)
