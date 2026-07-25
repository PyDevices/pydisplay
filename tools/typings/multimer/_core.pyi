from ._schedule import schedule as schedule
from ._ticks import ticks_diff as ticks_diff, ticks_ms as ticks_ms
from _typeshed import Incomplete

class _TimerCore:
    ONE_SHOT: Incomplete
    PERIODIC: Incomplete
    id: Incomplete
    def __init__(self, id: int = -1, **kwargs) -> None: ...
    def init(self, *, mode=..., freq: int = -1, period: int = -1, callback=None, hard: bool = True) -> None: ...
    def deinit(self) -> None: ...
