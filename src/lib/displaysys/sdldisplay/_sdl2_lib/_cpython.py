# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
A bare implementation of SDL2 written in CPython using ctypes.
"""

import ctypes
from sys import platform

from ._constants import *  # noqa: F403

# Load the SDL2 shared library using ctypes
if platform == "win32":
    _libSDL2 = ctypes.CDLL("SDL2.dll")
else:
    _libSDL2 = ctypes.CDLL("libSDL2-2.0.so.0")


###############################################################################
#                          SDL2 structs                                       #
###############################################################################


class SDL_Rect(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("w", ctypes.c_int),
        ("h", ctypes.c_int),
    ]


class SDL_Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int)]


class SDL_CommonEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint),
        ("timestamp", ctypes.c_uint),
        ("unused", ctypes.c_uint * 12),
    ]


class SDL_KeyboardEvent(ctypes.Structure):
    class Key(ctypes.Structure):
        class SDL_Keysym(ctypes.Structure):
            _fields_ = [
                ("scancode", ctypes.c_int),
                ("sym", ctypes.c_int),
                ("mod", ctypes.c_uint16),
                ("unused", ctypes.c_uint),
            ]

        _fields_ = [
            ("windowID", ctypes.c_uint),
            ("state", ctypes.c_uint8),
            ("repeat", ctypes.c_uint8),
            ("padding2", ctypes.c_uint8),
            ("padding3", ctypes.c_uint8),
            ("keysym", SDL_Keysym),
        ]

    _fields_ = [("type", ctypes.c_uint), ("timestamp", ctypes.c_uint), ("key", Key)]


class SDL_MouseMotionEvent(ctypes.Structure):
    class Motion(ctypes.Structure):
        _fields_ = [
            ("windowID", ctypes.c_uint),
            ("which", ctypes.c_uint),
            ("state", ctypes.c_uint),
            ("x", ctypes.c_int),
            ("y", ctypes.c_int),
            ("xrel", ctypes.c_int),
            ("yrel", ctypes.c_int),
        ]

    _fields_ = [
        ("type", ctypes.c_uint),
        ("timestamp", ctypes.c_uint),
        ("motion", Motion),
    ]


class SDL_MouseButtonEvent(ctypes.Structure):
    class Button(ctypes.Structure):
        _fields_ = [
            ("windowID", ctypes.c_uint),
            ("which", ctypes.c_uint),
            ("button", ctypes.c_uint8),
            ("state", ctypes.c_uint8),
            ("clicks", ctypes.c_uint8),
            ("padding", ctypes.c_uint8),
            ("x", ctypes.c_int),
            ("y", ctypes.c_int),
        ]

    _fields_ = [
        ("type", ctypes.c_uint),
        ("timestamp", ctypes.c_uint),
        ("button", Button),
    ]


class SDL_MouseWheelEvent(ctypes.Structure):
    class Wheel(ctypes.Structure):
        _fields_ = [
            ("windowID", ctypes.c_uint),
            ("which", ctypes.c_uint),
            ("x", ctypes.c_int),
            ("y", ctypes.c_int),
            ("direction", ctypes.c_uint),
            ("preciseX", ctypes.c_float),
            ("preciseY", ctypes.c_float),
        ]

    _fields_ = [("type", ctypes.c_uint), ("timestamp", ctypes.c_uint), ("wheel", Wheel)]


class SDL_JoyAxisEvent(ctypes.Structure):
    class JAxis(ctypes.Structure):
        _fields_ = [
            ("which", ctypes.c_int),
            ("axis", ctypes.c_uint8),
            ("padding1", ctypes.c_uint8),
            ("padding2", ctypes.c_uint8),
            ("padding3", ctypes.c_uint8),
            ("value", ctypes.c_int16),
            ("padding4", ctypes.c_uint16),
        ]

    _fields_ = [("type", ctypes.c_uint), ("timestamp", ctypes.c_uint), ("jaxis", JAxis)]


class SDL_JoyBallEvent(ctypes.Structure):
    class JBall(ctypes.Structure):
        _fields_ = [
            ("which", ctypes.c_int),
            ("ball", ctypes.c_uint8),
            ("padding1", ctypes.c_uint8),
            ("padding2", ctypes.c_uint8),
            ("padding3", ctypes.c_uint8),
            ("xrel", ctypes.c_int16),
            ("yrel", ctypes.c_int16),
        ]

    _fields_ = [("type", ctypes.c_uint), ("timestamp", ctypes.c_uint), ("jball", JBall)]


class SDL_JoyHatEvent(ctypes.Structure):
    class JHat(ctypes.Structure):
        _fields_ = [
            ("which", ctypes.c_int),
            ("hat", ctypes.c_uint8),
            ("value", ctypes.c_uint8),
            ("padding1", ctypes.c_uint8),
            ("padding2", ctypes.c_uint8),
        ]

    _fields_ = [("type", ctypes.c_uint), ("timestamp", ctypes.c_uint), ("jhat", JHat)]


class SDL_JoyButtonEvent(ctypes.Structure):
    class JButton(ctypes.Structure):
        _fields_ = [
            ("which", ctypes.c_int),
            ("button", ctypes.c_uint8),
            ("state", ctypes.c_uint8),
            ("padding1", ctypes.c_uint8),
            ("padding2", ctypes.c_uint8),
        ]

    _fields_ = [("type", ctypes.c_uint), ("timestamp", ctypes.c_uint), ("jbutton", JButton)]


###############################################################################
#                          SDL2 functions                                     #
###############################################################################

# SDL misc functions
_libSDL2.SDL_Init.argtypes = [ctypes.c_uint]
_libSDL2.SDL_Init.restype = ctypes.c_int
SDL_Init = _libSDL2.SDL_Init

_libSDL2.SDL_Quit.argtypes = []
_libSDL2.SDL_Quit.restype = None
SDL_Quit = _libSDL2.SDL_Quit

_libSDL2.SDL_GetError.argtypes = []
_libSDL2.SDL_GetError.restype = ctypes.c_char_p
SDL_GetError = _libSDL2.SDL_GetError

_libSDL2.SDL_PollEvent.argtypes = [ctypes.POINTER(SDL_CommonEvent)]
_libSDL2.SDL_PollEvent.restype = ctypes.c_int
SDL_PollEvent = _libSDL2.SDL_PollEvent

_libSDL2.SDL_InitSubSystem.argtypes = [ctypes.c_uint]
_libSDL2.SDL_InitSubSystem.restype = ctypes.c_int
SDL_InitSubSystem = _libSDL2.SDL_InitSubSystem

# SDL joystick functions
_libSDL2.SDL_NumJoysticks.argtypes = []
_libSDL2.SDL_NumJoysticks.restype = ctypes.c_int
SDL_NumJoysticks = _libSDL2.SDL_NumJoysticks

_libSDL2.SDL_JoystickOpen.argtypes = [ctypes.c_int]
_libSDL2.SDL_JoystickOpen.restype = ctypes.c_void_p
SDL_JoystickOpen = _libSDL2.SDL_JoystickOpen

_libSDL2.SDL_JoystickClose.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_JoystickClose.restype = None
SDL_JoystickClose = _libSDL2.SDL_JoystickClose

_libSDL2.SDL_JoystickInstanceID.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_JoystickInstanceID.restype = ctypes.c_int
SDL_JoystickInstanceID = _libSDL2.SDL_JoystickInstanceID

# SDL key functions
_libSDL2.SDL_GetKeyName.argtypes = [ctypes.c_int]
_libSDL2.SDL_GetKeyName.restype = ctypes.c_char_p
SDL_GetKeyName = _libSDL2.SDL_GetKeyName

_libSDL2.SDL_GetKeyFromName.argtypes = [ctypes.c_char_p]
_libSDL2.SDL_GetKeyFromName.restype = ctypes.c_int
SDL_GetKeyFromName = _libSDL2.SDL_GetKeyFromName

# SDL window functions
_libSDL2.SDL_CreateWindow.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint,
]
_libSDL2.SDL_CreateWindow.restype = ctypes.c_void_p
SDL_CreateWindow = _libSDL2.SDL_CreateWindow

_libSDL2.SDL_DestroyWindow.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_DestroyWindow.restype = None
SDL_DestroyWindow = _libSDL2.SDL_DestroyWindow

_libSDL2.SDL_SetWindowSize.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_libSDL2.SDL_SetWindowSize.restype = None
SDL_SetWindowSize = _libSDL2.SDL_SetWindowSize

# SDL renderer functions
_libSDL2.SDL_CreateRenderer.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint]
_libSDL2.SDL_CreateRenderer.restype = ctypes.c_void_p
SDL_CreateRenderer = _libSDL2.SDL_CreateRenderer

_libSDL2.SDL_DestroyRenderer.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_DestroyRenderer.restype = None
SDL_DestroyRenderer = _libSDL2.SDL_DestroyRenderer

_libSDL2.SDL_SetRenderDrawColor.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.c_uint,
    ctypes.c_uint,
    ctypes.c_uint,
]
_libSDL2.SDL_SetRenderDrawColor.restype = ctypes.c_int
SDL_SetRenderDrawColor = _libSDL2.SDL_SetRenderDrawColor

_libSDL2.SDL_SetRenderTarget.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_libSDL2.SDL_SetRenderTarget.restype = ctypes.c_int
SDL_SetRenderTarget = _libSDL2.SDL_SetRenderTarget

_libSDL2.SDL_RenderClear.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_RenderClear.restype = ctypes.c_int
SDL_RenderClear = _libSDL2.SDL_RenderClear

_libSDL2.SDL_RenderCopy.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(SDL_Rect),
    ctypes.POINTER(SDL_Rect),
]
_libSDL2.SDL_RenderCopy.restype = ctypes.c_int
SDL_RenderCopy = _libSDL2.SDL_RenderCopy

_libSDL2.SDL_RenderCopyEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(SDL_Rect),
    ctypes.POINTER(SDL_Rect),
    ctypes.c_double,
    ctypes.POINTER(SDL_Point),
    ctypes.c_int,
]
_libSDL2.SDL_RenderCopyEx.restype = ctypes.c_int
SDL_RenderCopyEx = _libSDL2.SDL_RenderCopyEx

_libSDL2.SDL_RenderPresent.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_RenderPresent.restype = None
SDL_RenderPresent = _libSDL2.SDL_RenderPresent

_libSDL2.SDL_RenderFillRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(SDL_Rect)]
_libSDL2.SDL_RenderFillRect.restype = ctypes.c_int
SDL_RenderFillRect = _libSDL2.SDL_RenderFillRect

_libSDL2.SDL_RenderSetLogicalSize.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_int,
]
_libSDL2.SDL_RenderSetLogicalSize.restype = ctypes.c_int
SDL_RenderSetLogicalSize = _libSDL2.SDL_RenderSetLogicalSize

# SDL texture functions
_libSDL2.SDL_CreateTexture.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
]
_libSDL2.SDL_CreateTexture.restype = ctypes.c_void_p
SDL_CreateTexture = _libSDL2.SDL_CreateTexture

_libSDL2.SDL_DestroyTexture.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_DestroyTexture.restype = None
SDL_DestroyTexture = _libSDL2.SDL_DestroyTexture

_libSDL2.SDL_SetTextureBlendMode.argtypes = [ctypes.c_void_p, ctypes.c_int]
_libSDL2.SDL_SetTextureBlendMode.restype = ctypes.c_int
SDL_SetTextureBlendMode = _libSDL2.SDL_SetTextureBlendMode

_libSDL2.SDL_UpdateTexture.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(SDL_Rect),
    ctypes.c_void_p,
    ctypes.c_int,
]
_libSDL2.SDL_UpdateTexture.restype = ctypes.c_int
SDL_UpdateTexture = _libSDL2.SDL_UpdateTexture

# SDL timer functions
_libSDL2.SDL_AddTimer.argtypes = [ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
_libSDL2.SDL_AddTimer.restype = ctypes.c_void_p
SDL_AddTimer = _libSDL2.SDL_AddTimer

_libSDL2.SDL_RemoveTimer.argtypes = [ctypes.c_void_p]
_libSDL2.SDL_RemoveTimer.restype = ctypes.c_int
SDL_RemoveTimer = _libSDL2.SDL_RemoveTimer

SDL_TimerCallback = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p)


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
        return SDL_CommonEvent.from_buffer(ctypes.create_string_buffer(56))

    event_type = event.type

    if event_type in _event_struct_map:
        return _event_struct_map[event_type].from_buffer(event)
    return SDL_CommonEvent.from_buffer(event)
