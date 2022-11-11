Changelog
=========
2.0.2 (2022-11-11)
------------------
- use https:// instead of git:// in pre-commit URLs - PR #50

2.0.1 (2020-10-10)
------------------
- Require at least Python 3.6 - PR #47

2.0.0 (2020-10-09)
------------------
- Cache aiohttp client session on the loop, not globally - PR #42. Thanks Nick Gaya for your contribution!
- Remove support for Python 3.5 - PR #45
- Add support for Python 3.8 - PR #46

1.5.0 (2020-03-31)
------------------
- | Implement support for request option ``follow_redirects``, disable following redirects by default - PR #41
  | While this is a behavior change, it matches what bravado's default HTTP client does starting with version 10.6.0, and is considered a bugfix.

1.4.2 (2019-06-27)
------------------
- Lazily initialize the event loop thread and the aiohttp ClientSession object, making sure this happens post-fork - PR #34

1.4.1 (2019-04-26)
------------------
- Add support for HttpFuture.cancel() from bravado 10.3.0 - PR #27
- Remove workaround code for file uploads that is no longer required, and might cause issues sometimes - PR #30

1.4.0 (2019-01-09)
------------------
- Add support for connect timeouts. This requires at least aiohttp 3.3, which in turn requires at least Python 3.5.3. - Issue #24, PR #25
- Removed support for aiohttp versions below 3.3, and Python versions below 3.5.3.

1.3.0 (2018-10-17)
------------------
- Support customizing or disabling TLS/SSL verification - PR #21

1.2.0 (2018-07-02)
------------------
- Support the new BravadoConnectionError introduced with bravado 10.1.0 - PR #18
- Convert non-string headers to strings - PR #18

1.1.0 (2018-06-15)
------------------
- Adapt to the new RequestConfig interface introduced by bravado. Requires at least bravado 10.0.0 - PR #17

1.0.0 (2018-05-28)
------------------
- bravado-asyncio has worked reliably internally, let's release it as 1.0.

0.4.3 (2018-03-08)
------------------
- One more try at fixing the remaining installation issues on Python < 3.5.3 - PR #15

0.4.2 (2018-03-07)
------------------
- Fix installation of bravado-asyncio with Python versions below 3.5.3 - PR #12, #13, #14

0.4.1 (2018-02-19)
------------------
- Only set Content-Type header if the request method is PUT or POST - PR #11

0.4.0 (2018-01-29)
------------------
- Add support for full asyncio run mode, to be used by the aiobravado library - PR #7
- Created documentation; find it at https://bravado-asyncio.readthedocs.io/en/latest/ - PR #7
- Document known issues, disable flaky request options timeout test PR #8, #10

0.3.4 (2018-01-22)
------------------
- Add support for setting a timeout through request_options - PR #6

0.3.3 (2018-01-04)
------------------
- Support ``collectionFormat: multi`` for array formData params as well - PR #4

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
