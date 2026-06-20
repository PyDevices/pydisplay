"""
lv_test_timer_sync.py

LVGL timer test — sync only (no run_queued loop).

Works on MCU, MicroPython unix, and CPython Linux where the default
multimer.Timer delivers callbacks without a run_queued() drain loop.

On platforms where Timer.REQUIRES_RUN_QUEUED is True (e.g. CPython
Win/mac), this script exits with a message — use lv_test_timer_queued.py
or lv_test_timer_async.py instead.
"""

import board_config

board_config.TIMER_ASYNC = False

from multimer import Timer

if getattr(Timer, "REQUIRES_RUN_QUEUED", False):
    print("lv_test_timer_sync: default Timer requires run_queued() on this platform.")
    print("Use lv_test_timer_queued.py instead, or lv_test_timer_async.py with asyncio.")
    raise SystemExit(1)

import display_driver  # noqa: F401
from lv_test_timer_common import build_ui

build_ui()
