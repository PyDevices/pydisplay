from _typeshed import Incomplete
from displaysys.sdldisplay import SDLDisplay

__all__ = ['AndroidSDLDisplay']

class AndroidSDLDisplay(SDLDisplay):
    quit_chord: Incomplete
    def __init__(self, width: int = 320, height: int = 240, rotation: int = 0, color_depth: int = 16, title: str = 'SDL2 Display', scale: float = 1.0, window_flags=..., render_flags=..., x=..., y=..., *, quiet: bool = False) -> None: ...
    def show(self, _timer=None) -> None: ...
    def init(self) -> None: ...
