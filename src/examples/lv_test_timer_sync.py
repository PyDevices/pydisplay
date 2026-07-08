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
from multimer import sleep_ms

while True:
    runtime.poll()
    sleep_ms(0)
    if runtime.quit_requested:
        break
    if getattr(display_drv, "_deinitialized", False):
        break
