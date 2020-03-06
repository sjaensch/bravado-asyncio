import sys

import aiohttp.client_exceptions
import pytest
from bravado.testing.integration_test import IntegrationTestsBaseClass
from bravado.testing.integration_test import ROUTE_1_RESPONSE

from bravado_asyncio.future_adapter import FutureAdapter
from bravado_asyncio.http_client import AsyncioClient


@pytest.mark.xfail(
    sys.platform != "linux",
    reason="These integration tests are flaky (run into TimeoutErrors) on Windows and macOS on Azure Pipelines",
)
class TestServerBravadoAsyncioClient(IntegrationTestsBaseClass):

    http_client_type = AsyncioClient
    http_future_adapter_type = FutureAdapter
    connection_errors_exceptions = {aiohttp.ClientConnectionError()}

    def test_bytes_header(self, swagger_http_server):
        # TODO: integrate this test into bravado integration tests suite
        response = self.http_client.request(
            {
                "method": "GET",
                "headers": {"byte-header": b"1"},
                "url": "{server_address}/1".format(server_address=swagger_http_server),
                # setting high timeouts here so we don't get coverage errors on Windows on Azure Pipelines
                "params": {"timeout": 5, "connect_timeout": 1},
            }
        ).result(timeout=5)

        assert response.text == self.encode_expected_response(ROUTE_1_RESPONSE)

    @pytest.mark.xfail(reason="Test started failing")
    def test_request_timeout_errors_are_thrown_as_BravadoTimeoutError(
        self, swagger_http_server
    ):
        super().test_request_timeout_errors_are_thrown_as_BravadoTimeoutError(
            swagger_http_server
        )
