# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
SDL2 timer backend — CPython fallback after ``_librt`` and ``_threading``.

Selected only when those backends are unavailable. Requires ``usdl2`` (native
module or ``add_ons/usdl2.py``); it is an import dependency, not a selection
criterion.
"""

from usdl2 import (
    SDL_INIT_TIMER,
    SDL_AddTimer,
    SDL_InitSubSystem,
    SDL_RemoveTimer,
    SDL_TimerCallback,
)

from ._timerbase import _TimerBase

_sdl2_timer_inited = False


def _ensure_sdl2_timer():
    """Initialize the SDL2 timer subsystem once (safe to call repeatedly)."""
    global _sdl2_timer_inited
    if _sdl2_timer_inited:
        return
    SDL_InitSubSystem(SDL_INIT_TIMER)
    _sdl2_timer_inited = True


class Timer(_TimerBase):
    """SDL2 Timer class"""

    BACKEND = "sdl2"
    NEEDS_PUMP = True

    def _start(self):
        _ensure_sdl2_timer()
        self._handler_ref = self._handler
        self._tcb = SDL_TimerCallback(self._handler_ref)
        self._timer = SDL_AddTimer(self._interval, self._tcb, None)

    def _stop(self):
        if self._timer:
            SDL_RemoveTimer(self._timer)
            self._timer = None
            self._tcb = None
            self._handler_ref = None
