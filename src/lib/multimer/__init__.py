# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`multimer`
====================================================

Cross-platform Timer class for *Python.

Enables using 'from multimer import Timer' on MicroPython on microcontrollers,
on MicroPython on Unix (which doesn't have a machine.Timer) and CPython (ditto).

_librt.py uses MicroPython ffi to connect to libc and librt, while _sdl2.py uses
SDL2 on CPython to connect to libSDL2.  CircuitPython unix uses _aio.py (thread-based;
see that module for why usdl2.add_timer is not used here).

Returns None if the platform is not supported rather than raising an ImportError so that
the client can handle the error more gracefully (e.g. by using `if Timer is not None:`).

Usage:
    from multimer import Timer
    tim = Timer()
    tim.init(mode=Timer.PERIODIC, period=500, callback=lambda t: print("."))
    ....
    tim.deinit()
"""

import sys

try:
    from machine import Timer  # MicroPython on microcontrollers
except ImportError:
    if sys.implementation.name == "micropython":  # MicroPython on Unix
#        from ._aio import Timer
        from ._librt import Timer
    elif sys.implementation.name == "cpython":  # Big Python
#        from ._aio import Timer
        from ._sdl2 import Timer
    elif sys.implementation.name == "circuitpython":
        from ._aio import Timer
    else:
        Timer = None

_next_timer_id = 1


def get_timer(callback, period=33):
    """
    Creates and returns a timer to periodically call the callback function

    Args:
        callback (function): The function to call periodically
        period (int): The period in milliseconds, default is 33ms (30fps)
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
    return t
