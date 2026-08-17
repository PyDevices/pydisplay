from . import AsyncTimer
from _typeshed import Incomplete

__all__ = ['Timer', 'is_async', 'name', 'pump', 'sleep_ms', 'uses_interrupts']

class _AsyncProvider:
    Timer = AsyncTimer
    name: str
    uses_interrupts: bool
    is_async: bool
    sleep_ms: Incomplete
    @staticmethod
    def pump() -> None: ...

Timer: Incomplete
name: Incomplete
uses_interrupts: Incomplete
is_async: Incomplete
sleep_ms: Incomplete
pump: Incomplete
