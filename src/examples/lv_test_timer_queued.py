"""
lv_test_timer_queued.py

LVGL timer test — default multimer.Timer with a run_queued() drain loop.

Use on CPython Win/mac and other platforms where timer callbacks are
delivered via the thread-to-main queue.  Harmless on MCU (run_queued is
a no-op on MicroPython).
"""

# Override board_config.TIMER_ASYNC for this timer test only. Real apps normally
# set this in board_config and can omit the import/assignment below.
import board_config

board_config.TIMER_ASYNC = False

import display_driver  # noqa: F401
from lv_test_timer_common import build_ui
from multimer import run_queued, sleep_ms

build_ui()

while True:
    run_queued()
    sleep_ms(1)
