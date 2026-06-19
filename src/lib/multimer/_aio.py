# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Thread-based software Timer for MicroPython-Unix and CPython."""

import sys
import time

from ._timerbase import _TimerBase

if sys.implementation.name == "cpython":
    from ._cpython_dispatch import schedule as _cpython_schedule
else:
    _cpython_schedule = None

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
    """Thread-based software Timer."""

    # lv_utils: run task_handler directly when not using main-thread dispatch.
    direct = _cpython_schedule is None

    def _start(self):
        self._running = True
        _spawn(self._loop)

    def _stop(self):
        self._running = False

    def _dispatch(self, arg):
        if _cpython_schedule is not None:
            _cpython_schedule(self._callback, arg)
        else:
            self._callback(arg)

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
                self._dispatch(self)
            except Exception:
                pass
            self._busy = False
            if self._mode == self.ONE_SHOT:
                self._running = False
                break
            next_t = _ticks_add(next_t, self._interval)
