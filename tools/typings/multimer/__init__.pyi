from ._async_timer import AsyncTimer as AsyncTimer
from ._schedule import schedule as schedule
from ._ticks import monotonic as monotonic, run_deadline_hook as run_deadline_hook, set_deadline_hook as set_deadline_hook, ticks_add as ticks_add, ticks_diff as ticks_diff, ticks_less as ticks_less, ticks_ms as ticks_ms
from ._timer import Timer as Timer
from _typeshed import Incomplete

__all__ = ['AsyncTimer', 'Timer', 'asyncio', 'monotonic', 'run_deadline_hook', 'schedule', 'set_deadline_hook', 'sleep_ms', 'ticks_add', 'ticks_diff', 'ticks_less', 'ticks_ms', 'uses_signals']

asyncio: Incomplete
sleep_ms: Incomplete

def uses_signals(): ...

