Changelog
=========

0.3.2 (2018-01-03)
------------------
- Add support for multiple values per query param (``collectionFormat: multi`` in OpenAPI/Swagger) - PR #3

0.3.1 (2017-11-15)
------------------
- Rework build system to specify Python versions explicitly; you'll need Python 3.6 for bravado-asyncio development - PR #2

0.3.0 (2017-11-13)
------------------
- Add support for msgpack as a wire protocol for responses - PR #1
- Timeout exceptions now inherit from ``bravado.exception.TimeoutError`` as well as the builtin ``TimeoutError`` if you
  use bravado 9.2.0 or higher - PR #1

0.2.0 (2017-09-28)
------------------
- Make sure file uploads work correctly when the data is coming from Pyramid
- Make sure query and form data values are strings
- Don't use Python 3.6 f-string syntax (stay compatible to Python 3.5)

0.1.0 (2017-07-28)
------------------
- Initial release
