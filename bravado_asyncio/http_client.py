import asyncio
import logging
import ssl
from collections.abc import Mapping
from typing import Any
from typing import Callable
from typing import cast
from typing import Dict
from typing import MutableMapping
from typing import Optional
from typing import Sequence
from typing import Type
from typing import Union

import aiohttp
from aiohttp.formdata import FormData
from bravado.config import RequestConfig
from bravado.http_client import HttpClient
from bravado.http_future import HttpFuture
from bravado_core.operation import Operation
from bravado_core.schema import is_list_like
from multidict import MultiDict
from yelp_bytes import from_bytes

from bravado_asyncio.definitions import RunMode
from bravado_asyncio.future_adapter import AsyncioFutureAdapter
from bravado_asyncio.future_adapter import BaseFutureAdapter
from bravado_asyncio.future_adapter import FutureAdapter
from bravado_asyncio.response_adapter import AioHTTPResponseAdapter
from bravado_asyncio.response_adapter import AsyncioHTTPResponseAdapter
from bravado_asyncio.thread_loop import get_thread_loop

log = logging.getLogger(__name__)


def get_client_session(loop: asyncio.AbstractEventLoop) -> aiohttp.ClientSession:
    """Get a shared ClientSession object that can be reused. If none exists yet it will
    create one using the passed-in loop.

    :param loop: an active (i.e. not closed) asyncio event loop
    :return: a ClientSession instance that can be used to do HTTP requests
    """
    try:
        return loop._bravado_asyncio_client_session  # type: ignore
    except AttributeError:
        client_session = aiohttp.ClientSession(loop=loop)
        loop._bravado_asyncio_client_session = client_session  # type: ignore
        return client_session


class AsyncioClient(HttpClient):
    """Asynchronous HTTP client using the asyncio event loop. Can either use an event loop
    in a separate thread or operate fully asynchronous within the current thread, using
    async / await.
    """

    def __init__(
        self,
        run_mode: RunMode = RunMode.THREAD,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        ssl_verify: Optional[Union[bool, str]] = None,
        ssl_cert: Optional[Union[str, Sequence[str]]] = None,
    ) -> None:
        """Instantiate a client using the given run_mode. If you do not pass in an event loop, then
        either a shared loop in a separate thread (THREAD mode) or the default asyncio
        event loop (FULL_ASYNCIO mode) will be used.
        Not passing in an event loop will make sure we share the :py:class:`aiohttp.ClientSession` object
        between AsyncioClient instances.

        :param ssl_verify: Set to False to disable SSL certificate validation. Provide the path to a
            CA bundle if you need to use a custom one.
        :param ssl_cert: Provide a client-side certificate to use. Either a sequence of strings pointing
            to the certificate (1) and the private key (2), or a string pointing to the combined certificate
            and key.
        """
        self.run_mode = run_mode
        self._loop = loop
        if self.run_mode == RunMode.THREAD:
            self.run_coroutine_func: Callable = asyncio.run_coroutine_threadsafe
            self.response_adapter = AioHTTPResponseAdapter
            self.bravado_future_class = HttpFuture
            self.future_adapter: Type[BaseFutureAdapter] = FutureAdapter
        elif run_mode == RunMode.FULL_ASYNCIO:
            from aiobravado.http_future import HttpFuture as AsyncioHttpFuture

            self.run_coroutine_func = asyncio.ensure_future
            self.response_adapter = AsyncioHTTPResponseAdapter
            self.bravado_future_class = AsyncioHttpFuture
            self.future_adapter = AsyncioFutureAdapter
        else:
            raise ValueError(
                "Don't know how to handle run mode {}".format(str(run_mode))
            )

        # translate the requests-type SSL options to a ssl.SSLContext object as used by aiohttp.
        # see https://aiohttp.readthedocs.io/en/stable/client_advanced.html#ssl-control-for-tcp-sockets
        if isinstance(ssl_verify, str) or ssl_cert:
            self.ssl_verify: Optional[bool] = None
            cafile = None
            if isinstance(ssl_verify, str):
                cafile = ssl_verify
            self.ssl_context: Optional[ssl.SSLContext] = ssl.create_default_context(
                cafile=cafile
            )
            if ssl_cert:
                if isinstance(ssl_cert, str):
                    ssl_cert = [ssl_cert]
                self.ssl_context.load_cert_chain(*ssl_cert)
        else:
            self.ssl_verify = ssl_verify
            self.ssl_context = None

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is not None:
            return self._loop
        elif self.run_mode == RunMode.THREAD:
            return get_thread_loop()
        elif self.run_mode == RunMode.FULL_ASYNCIO:
            return asyncio.get_event_loop()
        else:  # pragma: no cover
            # should be impossible because this is validated by __init__
            raise ValueError(self.run_mode)

    @property
    def client_session(self) -> aiohttp.ClientSession:
        return get_client_session(self.loop)

    def request(
        self,
        request_params: MutableMapping[str, Any],
        operation: Optional[Operation] = None,
        request_config: Optional[RequestConfig] = None,
    ) -> HttpFuture:
        """Sets up the request params for aiohttp and executes the request in the background.

        :param request_params: request parameters for the http request.
        :param operation: operation that this http request is for. Defaults
            to None - in which case, we're obviously just retrieving a Swagger
            Spec.
        :param request_config:RequestConfig request_config: Per-request config that is passed to
            :class:`bravado.http_future.HttpFuture`.

        :rtype: :class: `bravado_core.http_future.HttpFuture`
        """

        orig_data = request_params.get("data", {})
        if isinstance(orig_data, Mapping):
            data = FormData()
            for name, value in orig_data.items():
                str_value = (
                    str(value) if not is_list_like(value) else [str(v) for v in value]
                )
                data.add_field(name, str_value)
        else:
            data = orig_data

        if isinstance(data, FormData):
            for name, file_tuple in request_params.get("files", {}):
                stream_obj = file_tuple[1]
                data.add_field(name, stream_obj, filename=file_tuple[0])

        params = self.prepare_params(request_params.get("params"))

        connect_timeout: Optional[float] = request_params.get("connect_timeout")
        request_timeout: Optional[float] = request_params.get("timeout")
        # mypy thinks the type of total and connect is float, even though it is Optional[float]. Let's ignore the error.
        timeout = (
            aiohttp.ClientTimeout(total=request_timeout, connect=connect_timeout)
            if (connect_timeout or request_timeout)
            else None
        )

        follow_redirects = request_params.get("follow_redirects", False)

        # aiohttp always adds a Content-Type header, and this breaks some servers that don't
        # expect it for non-POST/PUT requests: https://github.com/aio-libs/aiohttp/issues/457
        skip_auto_headers = (
            ["Content-Type"]
            if request_params.get("method") not in ["POST", "PUT"]
            else None
        )

        coroutine = self.client_session.request(
            method=request_params.get("method") or "GET",
            url=cast(str, request_params.get("url", "")),
            params=params,
            data=data,
            headers={
                # Convert not string headers to string
                k: from_bytes(v) if isinstance(v, bytes) else str(v)
                for k, v in request_params.get("headers", {}).items()
            },
            allow_redirects=follow_redirects,
            skip_auto_headers=skip_auto_headers,
            timeout=timeout,
            **self._get_ssl_params()
        )

        future = self.run_coroutine_func(coroutine, loop=self.loop)

        return self.bravado_future_class(
            self.future_adapter(future),
            self.response_adapter(loop=self.loop),
            operation,
            request_config=request_config,
        )

    def prepare_params(
        self, params: Optional[Dict[str, Any]]
    ) -> Union[Optional[Dict[str, Any]], MultiDict]:
        if not params:
            return params

        items = []
        for key, value in params.items():
            entries = (
                [(key, str(value))]
                if not is_list_like(value)
                else [(key, str(v)) for v in value]
            )
            items.extend(entries)
        return MultiDict(items)

    def _get_ssl_params(self) -> Dict[str, Any]:
        return {"ssl": self.ssl_context if self.ssl_context else self.ssl_verify}
