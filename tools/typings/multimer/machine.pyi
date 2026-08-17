from machine import Timer as Timer

__all__ = ['Timer', 'name', 'uses_interrupts', 'is_async', 'pump', 'sleep_ms']

name: str
uses_interrupts: bool
is_async: bool

def pump() -> None: ...
def sleep_ms(ms) -> None: ...
