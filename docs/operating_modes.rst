Operating modes
===============

By default, :py:class:`~bravado_asyncio.http_client.AsyncioClient` operates as a drop-in replacement HTTP client for the bravado library.
It spins up a separate thread in which the asyncio event loop is run, and uses that to make concurrent requests.
However, it also supports a fully asynchronous mode, acting as the default HTTP client of the :any:`aiobravado`
library. In that operating mode, no separate thread is created, and the currently active event loop is used.
Please refer to the aiobravado documentation for usage instructions.
