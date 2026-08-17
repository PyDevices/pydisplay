from ._async_timer import AsyncTimer as AsyncTimer
from ._asyncio_loader import loop_running as loop_running
from ._schedule import schedule as schedule
from ._ticks import monotonic as monotonic, run_deadline_hook as run_deadline_hook, set_deadline_hook as set_deadline_hook, ticks_add as ticks_add, ticks_diff as ticks_diff, ticks_less as ticks_less, ticks_ms as ticks_ms

from _typeshed import Incomplete

asyncio: Incomplete

__all__ = ['AsyncTimer', 'asyncio', 'loop_running', 'monotonic', 'run_deadline_hook', 'schedule', 'set_deadline_hook', 'ticks_add', 'ticks_diff', 'ticks_less', 'ticks_ms']

