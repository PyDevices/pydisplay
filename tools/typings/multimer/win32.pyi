from ._core import _TimerCore

__all__ = ['name', 'uses_interrupts', 'is_async', 'pump', 'sleep_ms', 'Timer']

name: str
uses_interrupts: bool
is_async: bool

def pump() -> None: ...
def sleep_ms(ms) -> None: ...

class Timer(_TimerCore):
    def __init__(self, id: int = -1, **kwargs) -> None: ...
