# multimer types: queued, sync
"""
lv_test_timer_pump.py

LVGL timer test — default multimer.Timer with an unconditional pump() drain loop.

On CPython Linux and MicroPython unix (``_librt`` timers), callbacks
run on the main thread without a blocking loop — same as ``lv_test_timer_no_pump.py``.

On CPython Win/mac and other queued platforms, blocks in a ``pump()`` +
``broker.poll()`` loop.
"""

# Override board_config.TIMER_ASYNC for this timer test only. Real apps normally
# set this in board_config and can omit the import/assignment below.
import board_config

board_config.TIMER_ASYNC = False

import display_driver  # noqa: F401
from lv_test_timer_common import build_ui

build_ui("pump")

import time
import sys

from board_config import broker
from multimer import sleep_ms

_BROKER_POLL_S = 0.025
next_broker_poll = time.time() + _BROKER_POLL_S
_fast_spin = sys.implementation.name == "circuitpython"
loop_i = 0
while True:
    sleep_ms(1)
    loop_i += 1
    if _fast_spin:
        if time.time() >= next_broker_poll:
            broker.poll()
            next_broker_poll = time.time() + _BROKER_POLL_S
    elif (loop_i & 3) == 0:
        broker.poll()
