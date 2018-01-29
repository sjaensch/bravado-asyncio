Known issues
============

- The timeout value that you can specify as part of the
  `bravado request options <http://bravado.readthedocs.io/en/latest/configuration.html#per-request-configuration>`_
  is not always observed correctly by the underlying aiohttp client. This has been observed during integration tests
  with both Python 3.5 and Python 3.6.
- Due to the fact that network requests are done in non-blocking mode, a connect timeout cannot be specified. The
  corresponding parameter in request_options has no effect.
- The AsyncioClient does not support the ``set_basic_auth`` and ``set_api_key methods`` that the RequestsClient has.
  As a workaround, you can specify the necessary headers manually as part of the request options.
