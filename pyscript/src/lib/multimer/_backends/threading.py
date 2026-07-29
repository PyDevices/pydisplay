# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Thread-based software Timer."""

import sys

from .._core import _TimerCore
from .._schedule import schedule
from .._ticks import _sleep_ms, ticks_add, ticks_diff, ticks_ms

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
        try:
            import threading

            def _spawn(fn):
                threading.Thread(target=fn, daemon=True).start()

        except ImportError:
            raise ImportError("no thread support") from None


class Timer(_TimerCore):
    def __init__(self, id=-1, **kwargs):
        self._running = False
        super().__init__(id, **kwargs)

    def _wait_idle(self):
        while self._busy:
            _sleep_ms(1)

    def _arm(self):
        self._running = True
        _spawn(self._loop)

    def _disarm(self):
        self._running = False

    def _loop(self):
        next_t = ticks_add(ticks_ms(), self._period_ms)
        while self._running:
            delay = ticks_diff(next_t, ticks_ms())
            if delay > 0:
                _sleep_ms(delay)
            if not self._running:
                break
            self._busy = True
            try:
                schedule(self._invoke_callback, self)
            finally:
                self._busy = False
            if self._mode == self.ONE_SHOT:
                self._running = False
                self._armed = False
                break
            next_t = ticks_add(next_t, self._period_ms)
