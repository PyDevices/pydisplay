from ._events import events as events
from _typeshed import Incomplete

class TouchKeypad:
    x: Incomplete
    y: Incomplete
    w: Incomplete
    h: Incomplete
    cols: Incomplete
    rows: Incomplete
    key_width: Incomplete
    key_height: Incomplete
    areas: Incomplete
    def __init__(self, runtime, x, y, w, h, cols: int = 3, rows: int = 3, keys=None, translate=None, on_press=None, on_release=None) -> None: ...
    def callback(self, event) -> None: ...
    def read(self): ...
    def read_held(self): ...
