from .._core import _TimerCore
from .._schedule import schedule as schedule
from .._ticks import ticks_add as ticks_add, ticks_diff as ticks_diff, ticks_ms as ticks_ms

class Timer(_TimerCore): ...
