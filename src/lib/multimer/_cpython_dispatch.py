# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Defer timer callbacks to the main thread on CPython.

SDL_AddTimer and other background threads must not call LVGL or pydisplay
display code directly.  Timers enqueue work here; the main loop drains it via
poll().
"""

import queue

_pending = queue.SimpleQueue()


def schedule(cb, arg=0):
    """Queue a callback for execution on the main thread."""
    _pending.put((cb, arg))


def poll():
    """Run all queued callbacks.  Call from the main thread (e.g. display_driver.run)."""
    while True:
        try:
            cb, arg = _pending.get_nowait()
        except queue.Empty:
            break
        try:
            cb(arg)
        except Exception:
            pass
