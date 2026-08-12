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

_sdl2_timer_inited = False


def _backend_drain():
    import usdl2

    usdl2.SDL_PumpEvents()


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
        # usdl2's SDL trampoline already ``mp_sched_schedule``s onto the VM
        # thread before invoking this callback. Do not schedule again — with
        # ``hard=False`` (Runtime) that was a third hop and overflowed
        # ``MICROPY_SCHEDULER_DEPTH`` on micropython.exe.
        self._pending = False
        self._deliver()
        if self._mode is None or self._mode == self.ONE_SHOT:
            return 0
        return interval

    def _deliver(self):
        """Invoke the timer callback directly.

        Soft (``hard=False``) timers normally ``schedule`` again from
        ``_TimerCore._deliver``. That is redundant here: usdl2 already
        marshalled onto the VM thread, and the extra hop stalls LVGL under
        load on micropython.exe.
        """
        if self._busy:
            return
        self._busy = True
        try:
            self._invoke_callback(self)
        finally:
            self._busy = False
        if self._mode == self.ONE_SHOT:
            self.deinit()
