from collections.abc import Callable
from typing import Literal

__all__ = ["AutoDisplay", "host_kind"]

HostKind = Literal["pyscript", "jupyter", "desktop"]

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
) -> object: ...
