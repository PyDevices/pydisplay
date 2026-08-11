# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Windows waitable-timer backend (CPython + ``uwin32``).

APCs run on the main thread during an alertable wait. ``_backend_sleep_ms``
uses ``SleepEx`` so ``uses_signals()`` is True (librt analogue).
"""

import uwin32 as win

from .._core import _TimerCore

_uses_signals = True


def _backend_sleep_ms(ms):
    win.SleepEx(ms, True)


class Timer(_TimerCore):
    """Timer backed by ``CreateWaitableTimer`` / ``SetWaitableTimer``."""

    def __init__(self, id=-1, **kwargs):
        self._handle = None
        self._apc = None
        super().__init__(id, **kwargs)

    def _arm(self):
        self._handle = win.CreateWaitableTimerExW()
        self._apc = win.TIMERAPCROUTINE(self._on_apc)
        period = self._period_ms if self._mode == self.PERIODIC else 0
        win.SetWaitableTimer(self._handle, self._period_ms, period, self._apc, None)

    def _disarm(self):
        handle = self._handle
        self._handle = None
        self._apc = None
        if handle:
            try:
                win.CancelWaitableTimer(handle)
            except Exception:
                pass
            try:
                win.CloseHandle(handle)
            except Exception:
                pass

    def _on_apc(self, _arg, _low, _high):
        if self._mode is None:
            return
        self._deliver()
