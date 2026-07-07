# multimer types: sync
"""
lv_test_timer_sync.py

LVGL timer test — sync mode.

The board's shared broker timer drives LVGL (lv_utils subscribes its tick to it,
see add_ons/lv_utils.py), so there is no pump/no_pump distinction: the app loop
just needs one ``sleep_ms(0)`` per iteration plus a ``broker.poll()`` to service
input and quit.
"""

# Override board_config.TIMER_ASYNC for this timer test only. Real apps normally
# set this in board_config and can omit the import/assignment below.
import board_config

board_config.TIMER_ASYNC = False

import display_driver  # noqa: F401
from lv_test_timer_common import build_ui

build_ui("sync")

from board_config import broker, display_drv
from multimer import sleep_ms

while True:
    broker.poll()
    sleep_ms(0)
    # QUIT is handled via register_quit_cleanup when the window closes.
    if getattr(display_drv, "_deinitialized", False):
        break
