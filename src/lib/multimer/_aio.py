# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Thread-based software Timer for MicroPython-Unix (and CPython), signal-free."""

import time

from ._timerbase import _TimerBase

try:
    import _thread

    def _spawn(fn):
        _thread.start_new_thread(fn, ())
except ImportError:
    import threading

    def _spawn(fn):
        threading.Thread(target=fn, daemon=True).start()


try:
    _ticks_ms, _ticks_add, _ticks_diff, _sleep_ms = (
        time.ticks_ms,
        time.ticks_add,
        time.ticks_diff,
        time.sleep_ms,
    )
except AttributeError:  # CPython

    def _ticks_ms():
        return int(time.monotonic() * 1000)

    def _ticks_add(t, d):
        return t + d

    def _ticks_diff(a, b):
        return a - b

    def _sleep_ms(ms):
        time.sleep(ms / 1000)


class Timer(_TimerBase):
    """Thread-based software Timer; callbacks run on a background thread."""

    direct = True  # marker: callback runs in a normal thread context, not IRQ/signal

    def _start(self):
        self._running = True
        _spawn(self._loop)

    def _stop(self):
        self._running = False

    def _loop(self):
        next_t = _ticks_add(_ticks_ms(), self._interval)
        while self._running:
            delay = _ticks_diff(next_t, _ticks_ms())
            if delay > 0:
                _sleep_ms(delay)
            if not self._running:
                break
            self._busy = True
            try:
                self._callback(self)
            except Exception:
                pass
            self._busy = False
            if self._mode == self.ONE_SHOT:
                self._running = False
                break
            next_t = _ticks_add(next_t, self._interval)
