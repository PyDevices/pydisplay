"""
touch_setup.py - hardware setup for micropython-touch using DisplayBuffer on displaydev.
See: https://github.com/peterhinch/micropython-touch

Fetches micropython-touch into utils/gui/ when needed.

Usage:
    import touch_setup  # creates display
    from gui.core.tgui import Screen, ssd
"""

import sys

from board_config import display_drv, runtime
from displaybuf import DisplayBuffer as SSD

import multimer
import pygraphics

# Peter Hinch's GUI modules import framebuf directly. Use the same FrameBuffer
# implementation as DisplayBuffer so Writer glyph buffers can be blitted to ssd.
sys.modules["framebuf"] = pygraphics
multimer.install_asyncio_compat()

# format = SSD.GS4_HMSB  # 4-bit (16 item) lookup table of 16-bit RGB565 colors; w*h/2 buffer
# format = SSD.GS8  # 256 8-bit RGB332 colors; w*h buffer
format = SSD.RGB565  # all 65,536 16-bit RGB565 colors; w*h*2 buffer

ssd = SSD(display_drv, format)


# enable screenshot functionality
def screenshot(event):
    if event.type == runtime.events.MOUSEBUTTONDOWN and event.button == 3:
        ssd.screenshot()


runtime.on(runtime.events.MOUSEBUTTONDOWN, screenshot)
# End screenshot functionality


class Poller:
    def __init__(self, poll_func):
        self._poll_func = poll_func
        self._touched = False
        self._release_pending = False
        self.col = None
        self.row = None

    def poll(self):
        # Browser pointer down/up events may both arrive in one event-pump pass.
        # Keep the pressed state visible for one GUI poll before releasing it.
        if self._release_pending:
            self._touched = False
            self._release_pending = False
        self._poll_func()
        return bool(self._touched)

    def callback(self, event):
        if (event.type == runtime.events.MOUSEMOTION and event.buttons[0] == 1) or (
            event.type == runtime.events.MOUSEBUTTONDOWN and event.button == 1
        ):
            self.col, self.row = event.pos
            self._touched = True
        elif event.type == runtime.events.MOUSEBUTTONUP and event.button == 1:
            self._release_pending = True


tpad = Poller(runtime.poll)
runtime.on(
    [runtime.events.MOUSEMOTION, runtime.events.MOUSEBUTTONDOWN, runtime.events.MOUSEBUTTONUP],
    tpad.callback,
)

# After SSD exists: gui.core.colors imports SSD from this module.
from fetch_ph_gui import fetch_ph_gui  # noqa: E402

if not fetch_ph_gui("micropython-touch"):
    raise ImportError("micropython-touch not in utils/gui/; install with mip or copy gui/")

from gui.core.tgui import Display  # noqa: E402

display = Display(ssd, tpad)
