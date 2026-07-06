# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""SDL2 timer backend using ``usdl2``."""

from usdl2 import (
    SDL_INIT_TIMER,
    SDL_AddTimer,
    SDL_InitSubSystem,
    SDL_RemoveTimer,
    SDL_TimerCallback,
)

from .._core import _TimerCore
from .._schedule import schedule

_sdl2_timer_inited = False


def _backend_drain():
    import usdl2

    usdl2.pump_scheduler(32)


def _ensure_sdl2_timer():
    """Initialize the SDL2 timer subsystem once."""
    global _sdl2_timer_inited
    if _sdl2_timer_inited:
        return
    SDL_InitSubSystem(SDL_INIT_TIMER)
    _sdl2_timer_inited = True


class Timer(_TimerCore):
    """Timer backed by SDL_AddTimer."""

    def __init__(self, id=-1, **kwargs):
        self._timer = 0
        self._timer_callback = None
        self._handler_ref = None
        self._pending = False
        super().__init__(id, **kwargs)

    def _arm(self):
        _ensure_sdl2_timer()
        self._handler_ref = self._handler
        self._timer_callback = SDL_TimerCallback(self._handler_ref)
        self._timer = SDL_AddTimer(self._period_ms, self._timer_callback, None)
        if not self._timer:
            self._timer_callback = None
            self._handler_ref = None
            raise OSError("SDL_AddTimer failed")

    def _disarm(self):
        if self._timer:
            SDL_RemoveTimer(self._timer)
            self._timer = 0
        self._timer_callback = None
        self._handler_ref = None
        self._pending = False

    def _handler(self, interval, _param=None):
        if self._mode is None:
            return 0
        if not self._pending:
            self._pending = True
            schedule(self._scheduled_deliver, None)
        if self._mode == self.ONE_SHOT:
            return 0
        return interval

    def _scheduled_deliver(self, _arg):
        self._pending = False
        if self._mode is None:
            return
        self._deliver()
