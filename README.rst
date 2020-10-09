.. image:: https://img.shields.io/travis/sjaensch/bravado-asyncio.svg
  :target: https://travis-ci.org/sjaensch/bravado-asyncio?branch=master

.. image:: https://coveralls.io/repos/github/sjaensch/bravado-asyncio/badge.svg?branch=master
  :target: https://coveralls.io/github/sjaensch/bravado-asyncio?branch=master

.. image:: https://img.shields.io/pypi/v/bravado-asyncio.svg
    :target: https://pypi.python.org/pypi/bravado-asyncio/
    :alt: PyPi version

.. image:: https://img.shields.io/pypi/pyversions/bravado-asyncio.svg
    :target: https://pypi.python.org/pypi/bravado-asyncio/
    :alt: Supported Python versions


bravado-asyncio
===============

*Note*: This is not a fork or reimplementation of bravado using asynchronous programming (like aiomysql is for PyMySQL).
The interface of bravado remains unchanged. If you're developing fully asynchronous applications, you should use
`aiobravado <https://github.com/sjaensch/aiobravado>`_ instead.

bravado-asyncio is an asynchronous HTTP client for the `bravado library <https://github.com/Yelp/bravado>`_.
It uses Python's asyncio and `aiohttp <http://aiohttp.readthedocs.io/en/stable/>`_ internally. It enables
you to do concurrent network requests with bravado, similar to the `fido client <https://github.com/Yelp/fido>`_.
Unlike fido, bravado-asyncio does not depend on crochet or twisted and uses Python 3's standard library
to implement asynchronous behavior.

`aiobravado <https://github.com/sjaensch/aiobravado>`_, the fully asynchronous version of bravado, uses ``bravado-asyncio`` internally as HTTP client.


Example usage
-------------

If you're familiar with bravado then all you need to do is switch out (or specify) your HTTP client:

.. code-block:: python

    from bravado_asyncio.http_client import AsyncioClient
    from bravado.client import SwaggerClient

    client = SwaggerClient.from_url(
        'http://petstore.swagger.io/v2/swagger.json',
        http_client=AsyncioClient(),
    )
    pet = client.pet.getPetById(petId=42).result()


Installation
------------

.. code-block:: bash

    # This will install bravado-asyncio and bravado
    $ pip install bravado-asyncio

    # To install bravado-asyncio with the optional cchardet and aiodns packages,
    # which are recommended by the underlying aiohttp package
    $ pip install bravado-asyncio[aiohttp_extras]


Project status
--------------

The project is successfully used in production at Yelp. We have an integration
test suite that not only covers bravado-asyncio behavior, but also makes sure that behavior is equal to the (default)
synchronous bravado HTTP client. That said, if you find a bug please file an issue!

Development and contributing
----------------------------

Developing ``bravado-asyncio`` requires a working installation of Python 3.6 with the
`virtualenv <https://virtualenv.pypa.io/en/stable/>`_ package being installed.
All other requirements will be installed in a virtualenv created in the ``venv`` directory.
We also expect `make <https://www.gnu.org/software/make/>`_ to be installed. If you do not have it and do not want
to install it then please refer to the `Makefile <https://github.com/sjaensch/bravado-asyncio/blob/master/Makefile>`_
as to what commands need to be run for each target.

1. Run ``make``. This will create the virtualenv you will use for development, with all runtime and development
   dependencies installed.
2. If you're using `aactivator <https://github.com/Yelp/aactivator>`_ then you will be prompted to activate the new
   environment, please do so. If you prefer not to use aactivator, do ``source .activate.sh``.
3. Make sure everything is set up correctly by running ``make test``.

Since ``make test`` will run tests with multiple Python versions, you'll get an error if one of them can't be found.
You can ask tox to run tests with a specific Python version like so:

.. code-block:: bash

     $ tox -e py38

This will run tests with Python 3.8.

We do run linters that currently require Python 3.6. You can run them with ``tox -e pre-commit``.

Travis (the continuous integration system) and Github Actions will run tests with all supported Python versions, on all
supported platforms (Linux, macOS, Windows). Make sure you don't write code that works only on certain platforms or
Python versions.

Great, you're ready to go! If you have an improvement or bugfix, please submit a pull request.


The event loop
--------------

``bravado-asyncio`` creates its own event loop in a separate thread. This is necessary as it is not possible to use the
main event loop - it would require a fork of bravado, making its public interface asynchronous. That said,
``bravado-asyncio`` and bravado should work well with your existing asyncio application.

You shouldn't normally need to interact with ``bravado-asyncio``'s event loop. If you do need to do so please use
``bravado_asyncio.http_client.get_loop()`` to retrieve it. Note that it won't be the currently active loop!


License
-------

Written by Stephan Jaensch and licensed under the BSD 3-clause license (see `LICENSE.txt <https://github.com/sjaensch/bravado-asyncio/blob/master/LICENSE.txt>`_).
