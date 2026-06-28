# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

import sys

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


from ._schedule import schedule

ON_CALLBACK_ERROR = "raise" if sys.implementation.name == "cpython" else "log"


class _TimerBase:
    """
    A class to create a timer with the same API and similar functionality to
    MicroPython's machine.Timer class.
    """

    PERIODIC = const(0)
    ONE_SHOT = const(1)
    BACKEND = "base"
    NEEDS_PUMP = False

    def __init__(self, id=-1, **kwargs):
        self.id = id
        self._busy = False
        self._timer = None
        if kwargs:
            self.init(**kwargs)

    @property
    def needs_pump(self):
        return getattr(type(self), "NEEDS_PUMP", False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.deinit()
        return False

    def init(self, *, mode, freq=-1, period=-1, callback=None):
        if mode in (self.ONE_SHOT, self.PERIODIC):
            self._mode = mode
        else:
            raise ValueError("Invalid timer mode")

        self._interval = int(1000 / freq) if freq > 0 else period
        if self._interval < 1:
            raise ValueError("Invalid freq or period")

        self._callback = callback
        self._start()

    def deinit(self):
        self._wait_for_callback()
        self._stop()
        self._mode = None
        self._interval = 0
        self._callback = None
        self._timer = None

    def _wait_for_callback(self):
        while self._busy:
            pass

    def _invoke_callback(self, arg):
        if self._callback is None:
            return
        try:
            self._callback(arg)
        except Exception as exc:
            if ON_CALLBACK_ERROR == "raise":
                raise
            if ON_CALLBACK_ERROR == "log":
                print("Timer callback error:", exc)

    def _handler(self, interval, param=None):
        if self._busy:
            return

        self._busy = True
        try:
            schedule(self._callback, self)
        except RuntimeError:
            pass
        self._busy = False

        if self._mode == self.ONE_SHOT:
            self.deinit()
            return 0
        return self._interval

    def _start(self):
        raise NotImplementedError("Subclasses must implement this method")

    def _stop(self):
        raise NotImplementedError("Subclasses must implement this method")
