Quickstart
==========

Installation
------------

.. code-block:: bash

    # This will install bravado-asyncio and bravado
    $ pip install bravado-asyncio

    # To install bravado-asyncio with the optional cchardet and aiodns packages,
    # which are recommended by the underlying aiohttp package
    $ pip install bravado-asyncio[aiohttp_extras]

If you're using bravado-asyncio in your project, you'll want to add it to your setup.py or requirements.txt.


Example usage
-------------

bravado-asyncio is a drop-in replacement for the standard HTTP client provided by bravado. Just pass it as an
argument to either :py:meth:`bravado.client.SwaggerClient.from_url` or :py:meth:`bravado.client.SwaggerClient.from_spec`:

.. code-block:: python

    from bravado_asyncio.http_client import AsyncioClient
    from bravado.client import SwaggerClient

    client = SwaggerClient.from_url(
        'http://petstore.swagger.io/v2/swagger.json',
        http_client=AsyncioClient(),
    )
    pet = client.pet.getPetById(petId=1).result()

To take advantage of asynchronous requests, create the futures first and call result on them afterwards:

.. code-block:: python

    pet_future = client.pet.getPetById(petId=1)
    inventory_future = client.store.getInventory()
    pet = pet_future.result(timeout=5)
    inventory = inventory_future.result(timeout=5)

The total time it takes for this code block to complete will be roughly equal to execution time of the slower
network request. With bravado's standard requests client, the total time would be the sum of the two execution
times.
