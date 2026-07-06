# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Small application-loop helpers for portable examples."""

import sys
import time

from multimer import AsyncTimer, Timer, sleep_ms, ticks_add, ticks_diff, ticks_ms

try:
    import pydisplay_test_mode  # type: ignore[import-not-found]

    _TEST_DURATION_S = pydisplay_test_mode.DURATION_S if pydisplay_test_mode.ENABLED else None
except ImportError:
    _TEST_DURATION_S = None

_periodics = []


def _default_display_drv():
    try:
        from board_config import display_drv

        return display_drv
    except ImportError:
        return None


def _impl_name():
    return getattr(sys.implementation, "name", "?")


def _use_fallback_timer(display_drv):
    if sys.platform == "win32":
        return True
    return _impl_name() == "micropython" and type(display_drv).__name__ == "SDLDisplay"


class _Periodic:
    def __init__(self, callback, period, async_=False, display_drv=None):
        self.callback = callback
        self.period = period
        self.async_ = async_
        self.display_drv = _default_display_drv() if display_drv is None else display_drv
        self.timer = None
        self.last_tick = ticks_ms()
        self._running = True

        TimerClass = AsyncTimer if async_ else Timer
        if TimerClass is not None and not _use_fallback_timer(self.display_drv):
            self.timer = TimerClass(-1)
            self.timer.init(mode=TimerClass.PERIODIC, period=period, callback=self.callback)

    def poll(self):
        if not self._running or self.timer is not None:
            return
        now = ticks_ms()
        if ticks_diff(now, self.last_tick) < self.period:
            return
        self.callback(self)
        self.last_tick = ticks_add(self.last_tick, self.period)

    def deinit(self):
        self._running = False
        if self.timer is not None:
            self.timer.deinit()
            self.timer = None
        if self in _periodics:
            _periodics.remove(self)


def periodic(callback, period=1000, async_=False, display_drv=None):
    """Call ``callback`` every ``period`` ms using a timer or loop fallback."""
    timer = _Periodic(callback, period, async_=async_, display_drv=display_drv)
    _periodics.append(timer)
    return timer


def _poll_periodics():
    for timer in tuple(_periodics):
        timer.poll()


def _deinit_periodics():
    for timer in tuple(_periodics):
        timer.deinit()


def _test_done(start_time):
    return _TEST_DURATION_S is not None and time.time() - start_time >= _TEST_DURATION_S


def run_forever(poll, delay_ms=20):
    """Run a polling loop until ``poll`` returns true or test mode expires."""
    start_time = time.time()
    try:
        while True:
            if poll() or _test_done(start_time):
                break
            _poll_periodics()
            sleep_ms(delay_ms)
    finally:
        _deinit_periodics()


async def run_forever_async(poll, delay_ms=20):
    """Async version of ``run_forever``."""
    from multimer import asyncio

    start_time = time.time()
    try:
        while True:
            if poll() or _test_done(start_time):
                break
            _poll_periodics()
            await asyncio.sleep(delay_ms / 1000)  # type: ignore[misc]
    finally:
        _deinit_periodics()


def dual_main(sync_main, async_main, async_mode=False):
    """
    Start either a sync or async application entrypoint.

    In async mode, the async entrypoint is scheduled on the active multimer
    asyncio loop and the created task is returned.  In sync mode, the sync
    entrypoint is called immediately and its return value is returned.
    """
    if async_mode:
        from multimer import asyncio

        return asyncio.create_task(async_main())
    return sync_main()
