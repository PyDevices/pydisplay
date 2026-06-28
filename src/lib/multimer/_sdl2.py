# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Timer using SDL2 for CPython with the same API as machine.Timer in MicroPython.
"""

import ctypes
from sys import platform

from ._timerbase import _TimerBase

if platform == "win32":
    _libSDL2 = ctypes.CDLL("SDL2.dll")
else:
    _libSDL2 = ctypes.CDLL("libSDL2-2.0.so.0")

SDL_INIT_TIMER = 0x00000001

_libSDL2.SDL_Init.argtypes = [ctypes.c_uint]
_libSDL2.SDL_Init.restype = ctypes.c_int
SDL_Init = _libSDL2.SDL_Init

_libSDL2.SDL_AddTimer.argtypes = [ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
_libSDL2.SDL_AddTimer.restype = ctypes.c_void_p
SDL_AddTimer = _libSDL2.SDL_AddTimer

_libSDL2.SDL_RemoveTimer.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_RemoveTimer.restype = ctypes.c_int
SDL_RemoveTimer = _libSDL2.SDL_RemoveTimer

SDL_TimerCallback = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p)


class Timer(_TimerBase):
    """SDL2 Timer class"""

    BACKEND = "sdl2"
    NEEDS_PUMP = True

    def _start(self):
        SDL_Init(SDL_INIT_TIMER)
        self._handler_ref = self._handler
        self._tcb = SDL_TimerCallback(self._handler_ref)
        self._timer = SDL_AddTimer(self._interval, self._tcb, None)

    def _stop(self):
        if self._timer:
            SDL_RemoveTimer(self._timer)
            self._timer = None
            self._tcb = None
            self._handler_ref = None
