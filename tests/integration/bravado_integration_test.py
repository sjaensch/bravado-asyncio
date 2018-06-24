import aiohttp.client_exceptions
from bravado.testing.integration_test import IntegrationTestsBaseClass

from bravado_asyncio.future_adapter import FutureAdapter
from bravado_asyncio.http_client import AsyncioClient


class TestServerBravadoAsyncioClient(IntegrationTestsBaseClass):

    http_client_type = AsyncioClient
    http_future_adapter_type = FutureAdapter
    connection_errors_exceptions = {
        aiohttp.client_exceptions.ClientError()
    }

    def cancel_http_future(self, http_future):
        http_future.future.future.cancel()
