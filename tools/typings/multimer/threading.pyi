from ._core import _TimerCore

__all__ = ['Timer', 'is_async', 'name', 'pump', 'sleep_ms', 'uses_interrupts']

name: str
uses_interrupts: bool
is_async: bool

def pump() -> None: ...
def sleep_ms(ms) -> None: ...

class Timer(_TimerCore):
    def __init__(self, id: int = -1, **kwargs) -> None: ...
