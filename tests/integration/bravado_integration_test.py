import sys

import aiohttp.client_exceptions
import pytest
from bravado.testing.integration_test import IntegrationTestsBaseClass
from bravado.testing.integration_test import ROUTE_1_RESPONSE

from bravado_asyncio.future_adapter import FutureAdapter
from bravado_asyncio.http_client import AsyncioClient


@pytest.mark.skipif(
    sys.platform != "linux" or sys.version_info >= (3, 7),
    reason="These integration tests are failing on newer Python versions due to trying to connect to ::1 first, and failing. On Windows, they run into timeouts",
)
class TestServerBravadoAsyncioClient(IntegrationTestsBaseClass):  # pragma: no cover

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

        assert response.text == self.encode_expected_response(
            ROUTE_1_RESPONSE
        )  # pragma: no cover
