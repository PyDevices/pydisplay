# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`multimer`
====================================================

Cross-platform Timer class for *Python.

Enables using 'from multimer import Timer' on MicroPython on microcontrollers,
on MicroPython on Unix (which doesn't have a machine.Timer) and CPython (ditto).

_librt.py uses MicroPython ffi to connect to libc and librt.  CPython uses
_sdl2.py (SDL2 timers with main-thread callback dispatch).
CircuitPython unix uses _threading.py.

Returns None if the platform is not supported rather than raising an ImportError so that
the client can handle the error more gracefully (e.g. by using `if Timer is not None:`).

Usage:
    from multimer import Timer, schedule, run_scheduled, ticks_ms, ticks_diff
    tim = Timer()
    tim.init(mode=Timer.PERIODIC, period=500, callback=lambda t: print("."))
    ....
    tim.deinit()

On CPython and CircuitPython, call ``run_scheduled()`` from the main thread to drain
scheduled callbacks (for example in an event loop).
"""

import sys

from ._schedule import REQUIRES_RUN_SCHEDULED, run_scheduled, schedule
from ._ticks import sleep_ms, ticks_add, ticks_diff, ticks_less, ticks_ms

try:
    from machine import Timer  # MicroPython on microcontrollers
except ImportError:
    if sys.implementation.name == "micropython":  # MicroPython on Unix
        from ._librt import Timer
    elif sys.implementation.name == "cpython":  # Big Python
        from ._sdl2 import Timer
    elif sys.implementation.name == "circuitpython":
        from ._threading import Timer
    else:
        Timer = None

_next_timer_id = 1


def get_timer(callback, period=33, *, warn=True):
    """
    Creates and returns a timer to periodically call the callback function

    Args:
        callback (function): The function to call periodically
        period (int): The period in milliseconds, default is 33ms (30fps)
        warn (bool): If True and this platform requires ``run_scheduled()``, print a
            reminder. Defaults to True.
    """
    global _next_timer_id
    if sys.platform == "rp2":
        id = -1
    else:
        id = _next_timer_id
        _next_timer_id += 1
    t = Timer(id)

    def _timer_cb(_t):
        callback()

    t.init(mode=Timer.PERIODIC, period=period, callback=_timer_cb)
    print(f"Timer:  timer started ({id=}, {period=})")
    if warn and getattr(Timer, "REQUIRES_RUN_SCHEDULED", False):
        print("Timer:  callbacks require run_scheduled(); call it from your main loop")
    return t
