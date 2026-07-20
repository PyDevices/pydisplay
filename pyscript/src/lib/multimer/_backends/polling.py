# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cooperative polling Timer (last-resort backend)."""

from .._core import _TimerCore
from .._schedule import schedule
from .._ticks import ticks_add, ticks_diff, ticks_ms

_active = []


class Timer(_TimerCore):
    def _arm(self):
        self._next = ticks_add(ticks_ms(), self._period_ms)
        if self not in _active:
            _active.append(self)

    def _disarm(self):
        try:
            _active.remove(self)
        except ValueError:
            pass


def _tick(max_items=None):
    """Advance due polling timers (internal). Returns callbacks dispatched."""
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
            schedule(timer._invoke_callback, timer)
        finally:
            timer._busy = False

        if timer._mode == timer.ONE_SHOT:
            timer._disarm()
            timer._armed = False
            break

        timer._next = ticks_add(timer._next, timer._period_ms)
        while ticks_diff(timer._next, now) <= 0:
            timer._next = ticks_add(timer._next, timer._period_ms)

    return fired


def _backend_drain():
    _tick()


def _backend_sleep_ms(ms):
    """Sleep while pumping due polling timers (CircuitPython / no-thread hosts)."""
    import time

    end = ticks_add(ticks_ms(), max(0, int(ms)))
    while ticks_diff(end, ticks_ms()) > 0:
        _tick()
        # coarse yield; supervisor.delay or time.sleep
        try:
            import supervisor

            supervisor.delay(1)
        except Exception:
            time.sleep(0.001)
