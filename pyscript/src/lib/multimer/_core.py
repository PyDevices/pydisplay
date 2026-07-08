# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared machine.Timer-compatible core (internal)."""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


from ._schedule import schedule
from ._ticks import _sleep_ms


class _TimerCore:
    """Internal base matching MicroPython machine.Timer semantics."""

    ONE_SHOT = const(0)
    PERIODIC = const(1)

    def __init__(self, id=-1, **kwargs):
        self.id = id
        self._mode = None
        self._period_ms = 0
        self._callback = None
        self._hard = True
        self._busy = False
        self._armed = False
        # Pre-bind for the soft (scheduled) path: evaluating ``self._invoke_callback``
        # allocates a bound method, which fails inside a locked-heap ISR/FFI
        # callback. Bind once here so scheduling touches only stored references.
        self._deliver_cb = self._invoke_callback
        if kwargs:
            self.init(**kwargs)

    def init(self, *, mode=PERIODIC, freq=-1, period=-1, callback=None, hard=True):
        if mode not in (self.ONE_SHOT, self.PERIODIC):
            raise ValueError("Invalid timer mode")

        if self._armed:
            self._disarm()

        period_ms = int(1000 / freq) if freq > 0 else period

        if period_ms < 1:
            raise ValueError("Invalid freq or period")

        self._mode = mode
        self._period_ms = period_ms
        self._callback = callback
        self._hard = hard
        self._arm()
        self._armed = True

    def deinit(self):
        self._wait_idle()
        if self._armed:
            self._disarm()
            self._armed = False
        self._mode = None
        self._period_ms = 0
        self._callback = None
        self._hard = True

    def _wait_idle(self):
        while self._busy:
            _sleep_ms(1)

    def _invoke_callback(self, arg):
        if self._callback is None:
            raise TypeError("'NoneType' object isn't callable")
        self._callback(arg)

    def _deliver(self):
        if self._busy:
            return

        self._busy = True
        try:
            if self._hard:
                self._invoke_callback(self)
            else:
                schedule(self._deliver_cb, self)
        finally:
            self._busy = False

        if self._mode == self.ONE_SHOT:
            self.deinit()
            return 0
        return self._period_ms

    def _arm(self):
        raise NotImplementedError

    def _disarm(self):
        raise NotImplementedError
