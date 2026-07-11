# pyscript packages: micropython-touch
"""
touch_gui_simpletest.py - Smoke test for micropython-touch on pydisplay.

``touch_setup`` fetches the GUI and creates ``Display`` with a mouse/touch Poller.
This oneshot only verifies the framebuffer path (full widget demos use Screen.change).
On PyScript the gallery loader pre-installs the package (see ``# pyscript packages:``).
"""

from board_config import runtime
import touch_setup  # noqa: F401 — fetch + Display
from gui.core.tgui import ssd
from gui.core.colors import RED, BLUE, GREEN
from multimer.loop import run_forever

ssd.fill(0)
ssd.line(0, 0, ssd.width - 1, ssd.height - 1, GREEN)
ssd.rect(0, 0, 15, 15, RED)
ssd.rect(ssd.width - 15, ssd.height - 15, 15, 15, BLUE)
ssd.show()


def poll():
    runtime.poll()
    return runtime.quit_requested


run_forever(poll, delay_ms=50)
