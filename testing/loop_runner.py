import asyncio
import threading

class LoopRunner(threading.Thread):
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        threading.Thread.__init__(self, name='Test loop runner')
        self.loop = loop

    def run(self) -> None:
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            if self.loop.is_running():
                self.loop.close()

    def stop(self) -> None:
        self.loop.call_soon_threadsafe(lambda: self.loop.stop())
