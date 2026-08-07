from collections.abc import Callable
from typing import Literal

__all__ = ["AutoDisplay", "AutoDisplayResult", "host_kind"]

HostKind = Literal["pyscript", "jupyter", "desktop"]

class AutoDisplayResult:
    display: object
    host_read: Callable[..., object]
    timer_async: bool
    host: HostKind
    def __init__(
        self,
        display: object,
        host_read: Callable[..., object],
        timer_async: bool,
        host: HostKind,
    ) -> None: ...

def host_kind() -> HostKind: ...
def AutoDisplay(
    width: int = 320,
    height: int = 240,
    rotation: int = 0,
    scale: float = 1.0,
    title: str = "displaysys",
    canvas_id: str = "display_canvas",
    *,
    quiet: bool = False,
) -> AutoDisplayResult: ...
