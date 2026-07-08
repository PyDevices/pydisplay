# multimer types: sync
"""
lv_test_timer_sync.py

LVGL timer test — sync mode.

The board's shared runtime timer drives LVGL (lv_utils subscribes its tick to it,
see add_ons/lv_utils.py), so there is no pump/no_pump distinction: the app loop
just needs one ``sleep_ms(0)`` per iteration plus a ``runtime.poll()`` to service
input and quit.
"""

import display_driver  # noqa: F401
from lv_test_timer_common import build_ui

build_ui("sync")

from board_config import display_drv, runtime
from multimer import sleep_ms, ticks_diff, ticks_ms

try:
    import pydisplay_test_mode as _ptm

    _test_duration_ms = int(_ptm.DURATION_S * 1000) if _ptm.ENABLED else None
except ImportError:
    _test_duration_ms = None

_test_start = ticks_ms() if _test_duration_ms is not None else None

while True:
    runtime.poll()
    sleep_ms(0)
    if runtime.quit_requested:
        break
    if _test_start is not None and ticks_diff(ticks_ms(), _test_start) >= _test_duration_ms:
        break
    if getattr(display_drv, "_deinitialized", False):
        break
