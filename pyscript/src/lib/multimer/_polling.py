# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cooperative polling Timer for MicroPython ports without ffi or threads."""

from ._schedule import schedule
from ._ticks import ticks_add, ticks_diff, ticks_ms
from ._timerbase import _TimerBase

_active = []


class Timer(_TimerBase):
    """Software timer advanced by ``pump()`` and ``sleep_ms()``."""

    BACKEND = "polling"
    NEEDS_PUMP = True

    def _start(self):
        self._next = ticks_add(ticks_ms(), self._interval)
        if self not in _active:
            _active.append(self)

    def _stop(self):
        try:
            _active.remove(self)
        except ValueError:
            pass

    def _dispatch(self, arg):
        schedule(self._invoke_callback, arg)


def _tick(max_items=None):
    """Fire due timers. Returns the number of callbacks dispatched."""
    if not _active:
        return 0

    now = ticks_ms()
    fired = 0
    for timer in tuple(_active):
        if max_items is not None and fired >= max_items:
            break
        if timer not in _active:
            continue
        if ticks_diff(timer._next, now) > 0:
            continue

        fired += 1
        timer._busy = True
        try:
            timer._dispatch(timer)
        finally:
            timer._busy = False

        if timer._mode == timer.ONE_SHOT:
            timer._stop()
            break

        timer._next = ticks_add(timer._next, timer._interval)
        while ticks_diff(timer._next, now) <= 0:
            timer._next = ticks_add(timer._next, timer._interval)

    return fired
