import ctypes
from .._core import _TimerCore
from _typeshed import Incomplete

kernel32: Incomplete
INFINITE: int
WAIT_OBJECT_0: int
THREAD_SET_CONTEXT: int

class _LARGE_INTEGER(ctypes.Structure): ...

def is_active(): ...
def process_apcs() -> None: ...
def sleep_ex(ms) -> None: ...

class Timer(_TimerCore):
    def __init__(self, id: int = -1, **kwargs) -> None: ...
