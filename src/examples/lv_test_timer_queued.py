# multimer types: queued, sync
"""
lv_test_timer_queued.py

LVGL timer test — default multimer.Timer with a pump() drain loop when
the platform requires it (``needs_pump()`` is True).

On CPython Linux and MicroPython unix (``_ctypes`` / ``_ffi`` timers), callbacks
run on the main thread without a blocking loop — same as ``lv_test_timer_sync.py``.

On CPython Win/mac and other queued platforms, blocks in ``display_driver.run()``
(``pump()`` + ``broker.poll()``).
"""

# Override board_config.TIMER_ASYNC for this timer test only. Real apps normally
# set this in board_config and can omit the import/assignment below.
import board_config

board_config.TIMER_ASYNC = False

import display_driver  # noqa: F401
from lv_test_timer_common import build_ui
from multimer import Timer

build_ui()

if needs_pump():
    from display_driver import run

    run()
