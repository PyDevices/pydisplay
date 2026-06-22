# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`multimer`
====================================================

Cross-platform Timer class for *Python.

Enables using 'from multimer import Timer' on MicroPython on microcontrollers,
on MicroPython on Unix (which doesn't have a machine.Timer) and CPython (ditto).

_ffi.py uses MicroPython ffi to connect to libc and librt (MicroPython unix only).
MicroPython Windows and other ports without ffi or threads use _polling.py.
CPython on Linux uses _ctypes.py (POSIX librt via ctypes; callbacks on the main
thread without run_queued).  Other CPython ports use _threading.py (_sdl2.py if
threading is unavailable).  CircuitPython unix uses _threading.py.

Returns None if the platform is not supported rather than raising an ImportError so that
the client can handle the error more gracefully (e.g. by using `if Timer is not None:`).

Usage:
    from multimer import Timer, schedule, run_queued, ticks_ms, ticks_diff
    tim = Timer()
    tim.init(mode=Timer.PERIODIC, period=500, callback=lambda t: print("."))
    ....
    tim.deinit()

On CPython (non-Linux), CircuitPython, and MicroPython ports using the polling
backend, call ``run_queued()`` from the main thread to drain queued callbacks
(for example in an event loop).  ``sleep_ms()`` also advances polling timers.

For asyncio-based apps, use ``multimer.aio`` — see ``docs/concepts/multimer.md``.
"""

import sys

from ._schedule import REQUIRES_RUN_QUEUED, run_queued, schedule
from ._ticks import sleep_ms, ticks_add, ticks_diff, ticks_less, ticks_ms

DEBUG = True

try:
    from machine import Timer  # MicroPython on microcontrollers
except ImportError:
    if sys.implementation.name == "micropython":
        try:
            from ._ffi import Timer
        except ImportError:
            try:
                from ._threading import Timer
            except ImportError:
                from ._polling import Timer
    elif sys.implementation.name == "cpython":  # Big Python
        try:
            from ._ctypes import Timer
        except ImportError:
            try:
                from ._threading import Timer
            except ImportError:
                from ._sdl2 import Timer
    elif sys.implementation.name == "circuitpython":
        from ._threading import Timer
    else:
        Timer = None

_next_timer_id = 1


def get_timer(callback, period=33, *, asynchronous=None, warn=True):
    """
    Creates and returns a timer to periodically call the callback function

    Args:
        callback (function): The function to call periodically
        period (int): The period in milliseconds, default is 33ms (30fps)
        asynchronous (bool): If True, use ``multimer.aio.Timer``. If None or False,
            use the default ``Timer`` loaded at import.
        warn (bool): If True and this platform requires ``run_queued()``, print a
            reminder. Defaults to True.
    """
    global _next_timer_id
    if asynchronous:
        from multimer.aio import Timer as TimerCls
    else:
        TimerCls = Timer

    if sys.platform == "rp2":
        id = -1
    else:
        id = _next_timer_id
        _next_timer_id += 1
    t = TimerCls(id)

    def _timer_cb(_t):
        callback()

    t.init(mode=TimerCls.PERIODIC, period=period, callback=_timer_cb)
    if DEBUG:
        mod = getattr(TimerCls, "__module__", "?")
        name = getattr(TimerCls, "__qualname__", getattr(TimerCls, "__name__", "?"))
        print(f"Timer:  backend {mod}.{name}")
    print(f"Timer:  timer started ({id=}, {period=})")
    if warn and getattr(TimerCls, "REQUIRES_RUN_QUEUED", False):
        print("Timer:  callbacks require run_queued(); call it from your main loop")
    return t
