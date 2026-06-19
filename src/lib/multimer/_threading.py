# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Thread-based software Timer for MicroPython-Unix and CPython."""

import sys

from ._schedule import schedule
from ._ticks import sleep_ms, ticks_add, ticks_diff, ticks_ms
from ._timerbase import _TimerBase

if sys.implementation.name == "cpython":
    import threading

    def _spawn(fn):
        threading.Thread(target=fn, daemon=True).start()

else:
    try:
        import _thread

        def _spawn(fn):
            _thread.start_new_thread(fn, ())

    except ImportError:
        import threading

        def _spawn(fn):
            threading.Thread(target=fn, daemon=True).start()


class Timer(_TimerBase):
    """Thread-based software Timer."""

    def _start(self):
        self._running = True
        _spawn(self._loop)

    def _stop(self):
        self._running = False

    def _dispatch(self, arg):
        schedule(self._callback, arg)

    def _loop(self):
        next_t = ticks_add(ticks_ms(), self._interval)
        while self._running:
            delay = ticks_diff(next_t, ticks_ms())
            if delay > 0:
                sleep_ms(delay)
            if not self._running:
                break
            self._busy = True
            try:
                self._dispatch(self)
            except Exception:
                pass
            self._busy = False
            if self._mode == self.ONE_SHOT:
                self._running = False
                break
            next_t = ticks_add(next_t, self._interval)
