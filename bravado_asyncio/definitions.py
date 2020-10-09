from enum import Enum
from typing import NamedTuple
from typing import Optional

import aiohttp


class RunMode(Enum):
    THREAD = "thread"
    FULL_ASYNCIO = "full_asyncio"


class AsyncioResponse(NamedTuple):
    response: aiohttp.ClientResponse
    remaining_timeout: Optional[float]
