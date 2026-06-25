# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
SDL2 subset for MicroPython unix via ffi when the native usdl2 module is unavailable.
"""

import struct

import ffi
import uctypes

from ._constants import *  # noqa: F403

# Load the SDL2 shared library using ffi
_libSDL2 = ffi.open("libSDL2-2.0.so.0")


###############################################################################
#                          SDL2 structs                                       #
###############################################################################


def SDL_Rect(x=0, y=0, w=0, h=0):
    return struct.pack("iiii", x, y, w, h)


def SDL_Point(x=0, y=0):
    return struct.pack("ii", x, y)


SDL_CommonEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
}

SDL_KeyboardEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
    "key": (
        8,
        {
            "windowID": uctypes.UINT32 | 0,
            "state": uctypes.UINT8 | 4,
            "repeat": uctypes.UINT8 | 5,
            "padding2": uctypes.UINT8 | 6,
            "padding3": uctypes.UINT8 | 7,
            "keysym": (
                8,
                {
                    "scancode": 0 | uctypes.UINT32,
                    "sym": 4 | uctypes.UINT32,
                    "mod": 8 | uctypes.UINT16,
                    "unused": 10 | uctypes.UINT32,
                },
            ),
        },
    ),
}

SDL_MouseMotionEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
    "motion": (
        8,
        {
            "windowID": uctypes.UINT32 | 0,
            "which": uctypes.UINT32 | 4,
            "state": uctypes.UINT32 | 8,
            "x": uctypes.INT32 | 12,
            "y": uctypes.INT32 | 16,
            "xrel": uctypes.INT32 | 20,
            "yrel": uctypes.INT32 | 8,
        },
    ),
}

SDL_MouseButtonEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
    "button": (
        8,
        {
            "windowID": uctypes.UINT32 | 0,
            "which": uctypes.UINT32 | 4,
            "button": uctypes.UINT8 | 8,
            "state": uctypes.UINT8 | 9,
            "clicks": uctypes.UINT8 | 10,
            "padding1": uctypes.UINT8 | 11,
            "x": uctypes.INT32 | 12,
            "y": uctypes.INT32 | 16,
        },
    ),
}

SDL_MouseWheelEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
    "wheel": (
        8,
        {
            "windowID": uctypes.UINT32 | 0,
            "which": uctypes.UINT32 | 4,
            "x": uctypes.INT32 | 8,
            "y": uctypes.INT32 | 12,
            "direction": uctypes.UINT32 | 16,
            "preciseX": uctypes.FLOAT32 | 20,
            "preciseY": uctypes.FLOAT32 | 24,
        },
    ),
}

SDL_JoyAxisEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
    "jaxis": (
        8,
        {
            "which": uctypes.INT32 | 0,
            "axis": uctypes.UINT8 | 4,
            "value": uctypes.INT16 | 8,
        },
    ),
}

SDL_JoyBallEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
    "jball": (
        8,
        {
            "which": uctypes.INT32 | 0,
            "ball": uctypes.UINT8 | 4,
            "xrel": uctypes.INT16 | 8,
            "yrel": uctypes.INT16 | 10,
        },
    ),
}

SDL_JoyHatEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
    "jhat": (
        8,
        {
            "which": uctypes.INT32 | 0,
            "hat": uctypes.UINT8 | 4,
            "value": uctypes.UINT8 | 5,
        },
    ),
}

SDL_JoyButtonEvent = {
    "type": uctypes.UINT32 | 0,
    "timestamp": uctypes.UINT32 | 4,
    "jbutton": (
        8,
        {
            "which": uctypes.INT32 | 0,
            "button": uctypes.UINT8 | 4,
            "state": uctypes.UINT8 | 5,
        },
    ),
}


###############################################################################
#                          SDL2 functions                                     #
###############################################################################

# SDL misc functions
SDL_Init = _libSDL2.func("i", "SDL_Init", "I")
SDL_InitSubSystem = _libSDL2.func("i", "SDL_InitSubSystem", "I")
SDL_Quit = _libSDL2.func("v", "SDL_Quit", "")
SDL_GetError = _libSDL2.func("s", "SDL_GetError", "")
SDL_PollEvent = _libSDL2.func("i", "SDL_PollEvent", "P")

# SDL joystick functions
SDL_NumJoysticks = _libSDL2.func("i", "SDL_NumJoysticks", "")
SDL_JoystickOpen = _libSDL2.func("P", "SDL_JoystickOpen", "i")
SDL_JoystickClose = _libSDL2.func("v", "SDL_JoystickClose", "P")
SDL_JoystickInstanceID = _libSDL2.func("i", "SDL_JoystickInstanceID", "P")

# SDL key functions
SDL_GetKeyName = _libSDL2.func("s", "SDL_GetKeyName", "i")
SDL_GetKeyFromName = _libSDL2.func("i", "SDL_GetKeyFromName", "s")

# SDL window functions
SDL_CreateWindow = _libSDL2.func("P", "SDL_CreateWindow", "siiiii")
SDL_DestroyWindow = _libSDL2.func("v", "SDL_DestroyWindow", "P")
SDL_SetWindowSize = _libSDL2.func("v", "SDL_SetWindowSize", "Pii")

# SDL renderer functions
SDL_CreateRenderer = _libSDL2.func("P", "SDL_CreateRenderer", "PiI")
SDL_DestroyRenderer = _libSDL2.func("v", "SDL_DestroyRenderer", "P")
SDL_SetRenderDrawColor = _libSDL2.func("i", "SDL_SetRenderDrawColor", "PPPP")
SDL_SetRenderTarget = _libSDL2.func("i", "SDL_SetRenderTarget", "pP")
SDL_RenderClear = _libSDL2.func("v", "SDL_RenderClear", "P")
SDL_RenderCopy = _libSDL2.func("v", "SDL_RenderCopy", "PPPP")
SDL_RenderCopyEx = _libSDL2.func("v", "SDL_RenderCopyEx", "PPPPdPPi")
SDL_RenderPresent = _libSDL2.func("v", "SDL_RenderPresent", "P")
SDL_RenderFillRect = _libSDL2.func("i", "SDL_RenderFillRect", "PP")
SDL_RenderSetLogicalSize = _libSDL2.func("i", "SDL_RenderSetLogicalSize", "Pii")

# SDL texture functions
SDL_CreateTexture = _libSDL2.func("P", "SDL_CreateTexture", "PIiiii")
SDL_DestroyTexture = _libSDL2.func("v", "SDL_DestroyTexture", "P")
SDL_SetTextureBlendMode = _libSDL2.func("i", "SDL_SetTextureBlendMode", "PI")
SDL_UpdateTexture = _libSDL2.func("i", "SDL_UpdateTexture", "PPPi")

# SDL timer functions  NOT WORKING
SDL_AddTimer = _libSDL2.func("P", "SDL_AddTimer", "IPP")
SDL_RemoveTimer = _libSDL2.func("i", "SDL_RemoveTimer", "P")


def SDL_TimerCallback(tcb):
    return ffi.callback("I", tcb, "IP")


###############################################################################
#                          SDL event union                                    #
###############################################################################

_event_struct_map = {
    # Constants from _constants.py
    SDL_KEYDOWN: SDL_KeyboardEvent,  # noqa: F405
    SDL_KEYUP: SDL_KeyboardEvent,  # noqa: F405
    SDL_MOUSEMOTION: SDL_MouseMotionEvent,  # noqa: F405
    SDL_MOUSEBUTTONDOWN: SDL_MouseButtonEvent,  # noqa: F405
    SDL_MOUSEBUTTONUP: SDL_MouseButtonEvent,  # noqa: F405
    SDL_MOUSEWHEEL: SDL_MouseWheelEvent,  # noqa: F405
    SDL_JOYAXISMOTION: SDL_JoyAxisEvent,  # noqa: F405
    SDL_JOYBALLMOTION: SDL_JoyBallEvent,  # noqa: F405
    SDL_JOYHATMOTION: SDL_JoyHatEvent,  # noqa: F405
    SDL_JOYBUTTONDOWN: SDL_JoyButtonEvent,  # noqa: F405
    SDL_JOYBUTTONUP: SDL_JoyButtonEvent,  # noqa: F405
    SDL_POLLSENTINEL: SDL_CommonEvent,  # noqa: F405
}


def SDL_Event(event=None):
    """
    Convert event to an SDL_Event object using ctypes.
    The size of the largest SDL_Event struct is 56 bytes.
    """
    if event is None:
        return bytearray(56)  # Size of the largest SDL_Event struct

    event_type = int.from_bytes(event[:4], "little")

    if event_type in _event_struct_map:
        return uctypes.struct(uctypes.addressof(event), _event_struct_map[event_type])
    return uctypes.struct(uctypes.addressof(event), SDL_CommonEvent)
