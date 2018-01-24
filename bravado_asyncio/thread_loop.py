"""Module for creating a separate thread with an asyncio event loop running inside it."""
import asyncio
import threading
from typing import Optional  # noqa


# module variable holding a reference to the event loop
event_loop = None  # type: Optional[asyncio.AbstractEventLoop]


def run_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_thread_loop() -> asyncio.AbstractEventLoop:
    global event_loop
    if event_loop is None:
        event_loop = asyncio.new_event_loop()
        thread = threading.Thread(target=run_event_loop, args=(event_loop,), daemon=True)
        thread.start()
    return event_loop
