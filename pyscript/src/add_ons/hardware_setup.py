"""
hardware_setup.py - hardware setup for micropython-micro-gui using DisplayBuffer.
See: https://github.com/peterhinch/micropython-micro-gui

Fetches micropython-micro-gui into add_ons/gui/ when needed.

On desktop, navigation uses keyboard stand-ins (not GPIO pins):
  Tab / Right  — next control
  Left         — previous control
  Enter / Space — select / operate
  Up           — increase
  Down         — decrease

Usage:
    import hardware_setup  # creates display
    from gui.core.ugui import Screen, ssd
"""

from board_config import display_drv, runtime
from displaybuf import DisplayBuffer as SSD

# format = SSD.GS4_HMSB
# format = SSD.GS8
format = SSD.RGB565

ssd = SSD(display_drv, format)


def screenshot(event):
    if event.type == runtime.events.MOUSEBUTTONDOWN and event.button == 3:
        ssd.screenshot()


runtime.on(runtime.events.MOUSEBUTTONDOWN, screenshot)


class _StubBtn:
    """Pushbutton-compatible object for ugui.Display when not using machine.Pin."""

    def __init__(self):
        self._tf = False
        self._ff = False
        self._df = False
        self._ld = False
        self._ta = ()
        self._fa = ()
        self._da = ()
        self._la = ()

    def press_func(self, f=None, args=()):
        self._tf = f
        self._ta = args

    def release_func(self, f=None, args=()):
        self._ff = f
        self._fa = args

    def long_func(self, f=None, args=()):
        self._ld = f
        self._la = args

    def double_func(self, f=None, args=()):
        self._df = f
        self._da = args

    def _launch(self, f, args):
        if not f:
            return
        try:
            from gui.primitives import launch

            launch(f, args)
        except ImportError:
            if args:
                f(*args)
            else:
                f()

    def press(self):
        self._launch(self._tf, self._ta)

    def release(self):
        self._launch(self._ff, self._fa)


nxt = _StubBtn()
sel = _StubBtn()
prev = _StubBtn()
increase = _StubBtn()
decrease = _StubBtn()

# Key bindings: next/prev/select/increase/decrease
_KEYMAP = {}


def _bind_keys():
    try:
        from eventsys.keys import Keys
    except ImportError:
        return
    _KEYMAP.update(
        {
            Keys.K_TAB: ("press", nxt),
            Keys.K_RIGHT: ("press", nxt),
            Keys.K_LEFT: ("press", prev),
            Keys.K_RETURN: ("release", sel),
            Keys.K_SPACE: ("release", sel),
            Keys.K_UP: ("press", increase),
            Keys.K_DOWN: ("press", decrease),
        }
    )


def _on_key(event):
    if event.type != runtime.events.KEYDOWN:
        return
    action = _KEYMAP.get(event.key)
    if action is None:
        return
    kind, btn = action
    if kind == "press":
        btn.press()
    else:
        btn.release()


_bind_keys()
runtime.on(runtime.events.KEYDOWN, _on_key)

# After SSD exists: gui.core.colors imports SSD from this module.
from fetch_ph_gui import fetch_ph_gui  # noqa: E402

if not fetch_ph_gui("micropython-micro-gui"):
    raise ImportError("micropython-micro-gui not in add_ons/gui/; install with mip or copy gui/")

from gui.core.ugui import Display  # noqa: E402

display = Display(ssd, nxt, sel, prev, increase, decrease, touch=None)
