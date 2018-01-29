.. bravado-asyncio documentation master file, created by
   sphinx-quickstart on Wed Jan 24 16:31:20 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to bravado-asyncio's documentation!
===========================================

bravado-asyncio is an asynchronous HTTP client for the `bravado library <https://github.com/Yelp/bravado>`_.
It uses Python's asyncio and `aiohttp <http://aiohttp.readthedocs.io/en/stable/>`_ internally. It enables
you to do concurrent network requests with bravado, similar to the `fido client <https://github.com/Yelp/fido>`_.
Unlike fido, bravado-asyncio does not depend on crochet or twisted and uses Python 3's standard library
to implement asynchronous behavior.

`aiobravado <https://github.com/sjaensch/aiobravado>`_, the fully asynchronous version of bravado, uses bravado-asyncio internally as HTTP client.

.. toctree::
    :maxdepth: 1

    quickstart
    operating_modes
    known_issues
    changelog



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
