# multimer types: sync
"""
lv_test_timer_no_pump.py

LVGL timer test — no pump() loop.

Works on MCU, MicroPython unix, and CPython Linux where the default
multimer.Timer delivers callbacks without a pump() drain loop.

On platforms where ``needs_pump()`` is True (e.g. CPython macOS threading
backend), this script will hang — use lv_test_timer_pump.py or
lv_test_timer_async.py instead.  On Windows with ``multimer._win32``, the
main loop must use ``multimer.sleep_ms()`` (not ``time.sleep``) so APC timer
delivery can run.
"""

# Override board_config.TIMER_ASYNC for this timer test only. Real apps normally
# set this in board_config and can omit the import/assignment below.
import board_config

board_config.TIMER_ASYNC = False

import display_driver  # noqa: F401
from lv_test_timer_common import build_ui

build_ui()
