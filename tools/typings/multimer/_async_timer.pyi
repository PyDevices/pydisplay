from ._asyncio_loader import load_asyncio as load_asyncio, loop_running as loop_running
from ._core import _TimerCore

class AsyncTimer(_TimerCore):
    def __init__(self, id: int = -1, **kwargs) -> None: ...
