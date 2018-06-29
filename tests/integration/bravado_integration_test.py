import aiohttp.client_exceptions
from bravado.testing.integration_test import IntegrationTestsBaseClass
from bravado.testing.integration_test import ROUTE_1_RESPONSE

from bravado_asyncio.future_adapter import FutureAdapter
from bravado_asyncio.http_client import AsyncioClient


class TestServerBravadoAsyncioClient(IntegrationTestsBaseClass):

    http_client_type = AsyncioClient
    http_future_adapter_type = FutureAdapter
    connection_errors_exceptions = {
        aiohttp.ClientConnectionError(),
    }

    def cancel_http_future(self, http_future):
        http_future.future.future.cancel()

    def test_bytes_header(self, swagger_http_server):
        # TODO: integrate this test into bravado integration tests suite
        response = self.http_client.request({
            'method': 'GET',
            'headers': {'byte-header': b'1'},
            'url': '{server_address}/1'.format(server_address=swagger_http_server),
            'params': {},
        }).result(timeout=1)

        assert response.text == self.encode_expected_response(ROUTE_1_RESPONSE)
