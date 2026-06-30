# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
SDL2 timer backend (CPython last resort; also used when ``usdl2`` is built in).

Imports timer APIs from ``usdl2`` when available, otherwise binds
``SDL_AddTimer`` / ``SDL_RemoveTimer`` via ctypes against system libSDL2.
"""

from sys import platform

from ._timerbase import _TimerBase

try:
    from usdl2 import (
        SDL_INIT_TIMER,
        SDL_AddTimer,
        SDL_InitSubSystem,
        SDL_RemoveTimer,
        SDL_TimerCallback,
    )
except ImportError:
    try:
        import ctypes
    except ImportError as err:
        raise ImportError("multimer._sdl2 requires usdl2 or ctypes") from err

    if platform == "win32":
        _libSDL2 = ctypes.CDLL("SDL2.dll")
    else:
        _libSDL2 = ctypes.CDLL("libSDL2-2.0.so.0")

    SDL_INIT_TIMER = 0x00000001

    _libSDL2.SDL_InitSubSystem.argtypes = [ctypes.c_uint]
    _libSDL2.SDL_InitSubSystem.restype = ctypes.c_int
    SDL_InitSubSystem = _libSDL2.SDL_InitSubSystem

    _libSDL2.SDL_AddTimer.argtypes = [ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
    _libSDL2.SDL_AddTimer.restype = ctypes.c_void_p
    SDL_AddTimer = _libSDL2.SDL_AddTimer

    _libSDL2.SDL_RemoveTimer.argtypes = [ctypes.c_void_p]
    _libSDL2.SDL_RemoveTimer.restype = ctypes.c_int
    SDL_RemoveTimer = _libSDL2.SDL_RemoveTimer

    SDL_TimerCallback = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p)

_sdl2_timer_inited = False


def _ensure_sdl2_timer():
    """Initialize the SDL2 timer subsystem once (safe to call repeatedly)."""
    global _sdl2_timer_inited
    if _sdl2_timer_inited:
        return
    SDL_InitSubSystem(SDL_INIT_TIMER)
    _sdl2_timer_inited = True


_ensure_sdl2_timer()


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
