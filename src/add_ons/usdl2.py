# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Pure-Python ``usdl2`` implementation when the native C module is unavailable.

Shipped as ``add_ons/usdl2.py`` so MicroPython loads it via ``sys.path`` only when
the built-in/frozen ``usdl2`` module is not present. Uses ctypes on CPython and
MicroPython win32; ffi/uctypes on MicroPython unix.
"""

import sys

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


###############################################################################
#                          SDL2 Constants                                     #
###############################################################################

# SDL_WindowPos values
SDL_WINDOWPOS_UNDEFINED = const(0x1FFF0000)
SDL_WINDOWPOS_CENTERED = const(0x2FFF0000)

# SDL_Window flags
SDL_WINDOW_FULLSCREEN = const(0x00000001)
SDL_WINDOW_OPENGL = const(0x00000002)
SDL_WINDOW_SHOWN = const(0x00000004)
SDL_WINDOW_HIDDEN = const(0x00000008)
SDL_WINDOW_BORDERLESS = const(0x00000010)
SDL_WINDOW_RESIZABLE = const(0x00000020)
SDL_WINDOW_MINIMIZED = const(0x00000040)
SDL_WINDOW_MAXIMIZED = const(0x00000080)
SDL_WINDOW_INPUT_GRABBED = const(0x00000100)
SDL_WINDOW_INPUT_FOCUS = const(0x00000200)
SDL_WINDOW_MOUSE_FOCUS = const(0x00000400)
SDL_WINDOW_FULLSCREEN_DESKTOP = const(0x00001001)
SDL_WINDOW_ALLOW_HIGHDPI = const(0x00002000)
SDL_WINDOW_MOUSE_CAPTURE = const(0x00004000)
SDL_WINDOW_ALWAYS_ON_TOP = const(0x00008000)
SDL_WINDOW_SKIP_TASKBAR = const(0x00010000)
SDL_WINDOW_UTILITY = const(0x00020000)
SDL_WINDOW_TOOLTIP = const(0x00040000)
SDL_WINDOW_POPUP_MENU = const(0x00080000)
SDL_WINDOW_VULKAN = const(0x10000000)

# SDL_Renderer flags
SDL_RENDERER_SOFTWARE = const(0x00000001)
SDL_RENDERER_ACCELERATED = const(0x00000002)
SDL_RENDERER_PRESENTVSYNC = const(0x00000004)
SDL_RENDERER_TARGETTEXTURE = const(0x00000008)

# SDL_Init flags
SDL_INIT_TIMER = const(0x00000001)
SDL_INIT_AUDIO = const(0x00000010)
SDL_INIT_VIDEO = const(0x00000020)
SDL_INIT_JOYSTICK = const(0x00000200)
SDL_INIT_HAPTIC = const(0x00001000)
SDL_INIT_GAMECONTROLLER = const(0x00002000)
SDL_INIT_EVENTS = const(0x00004000)
SDL_INIT_EVERYTHING = const(0x0000000F)
SDL_INIT_NOPARACHUTE = const(0x00100000)

# SDL_Texture values
SDL_TEXTUREACCESS_STATIC = const(0)
SDL_TEXTUREACCESS_STREAMING = const(1)
SDL_TEXTUREACCESS_TARGET = const(2)

# SDL_BlendMode values
SDL_BLENDMODE_NONE = const(1)
SDL_BLENDMODE_BLEND = const(2)
SDL_BLENDMODE_ADD = const(3)
SDL_BLENDMODE_MOD = const(4)
SDL_BLENDMODE_MUL = const(5)

# SDL_Event types (not complete)
SDL_QUIT = const(0x100)  # User clicked the window close button
SDL_KEYDOWN = const(0x300)  # Key pressed
SDL_KEYUP = const(0x301)  # Key released
SDL_MOUSEMOTION = const(0x400)  # Mouse moved
SDL_MOUSEBUTTONDOWN = const(0x401)  # Mouse button pressed
SDL_MOUSEBUTTONUP = const(0x402)  # Mouse button released
SDL_MOUSEWHEEL = const(0x403)  # Mouse wheel motion
SDL_JOYAXISMOTION = const(0x600)  # Joystick axis motion
SDL_JOYBALLMOTION = const(0x601)  # Joystick trackball motion
SDL_JOYHATMOTION = const(0x602)  # Joystick hat position change
SDL_JOYBUTTONDOWN = const(0x603)  # Joystick button pressed
SDL_JOYBUTTONUP = const(0x604)  # Joystick button released
SDL_JOYDEVICEADDED = const(0x605)  # A joystick was connected
SDL_JOYDEVICEREMOVED = const(0x606)  # A joystick was disconnected
SDL_POLLSENTINEL = const(0x7F00)  # Signals the end of an event poll cycle

# SDL_MouseMotionEvent button masks
SDL_BUTTON_LMASK = const(1 << 0)  # Left mouse button
SDL_BUTTON_MMASK = const(1 << 1)  # Middle mouse button
SDL_BUTTON_RMASK = const(1 << 2)  # Right mouse button

# SDL_JoyHatEvent position masks
SDL_HAT_CENTERED = const(0x00)
SDL_HAT_UP = const(0x01)
SDL_HAT_RIGHT = const(0x02)
SDL_HAT_DOWN = const(0x04)
SDL_HAT_LEFT = const(0x08)


###############################################################################
#                          SDL2 Pixel Formats                                 #
###############################################################################


def SDL_DEFINE_PIXELFORMAT(type, order, layout, bits, bytes):
    """
    Define a pixel format.
    """
    return (
        (1 << 28)
        | ((type) << 24)
        | ((order) << 20)
        | ((layout) << 16)
        | ((bits) << 8)
        | ((bytes) << 0)
    )


# SDL_PIXELTYPE values
SDL_PIXELTYPE_UNKNOWN = const(0)
SDL_PIXELTYPE_INDEX1 = const(1)
SDL_PIXELTYPE_INDEX4 = const(2)
SDL_PIXELTYPE_INDEX8 = const(3)
SDL_PIXELTYPE_PACKED8 = const(4)
SDL_PIXELTYPE_PACKED16 = const(5)
SDL_PIXELTYPE_PACKED32 = const(6)
SDL_PIXELTYPE_ARRAYU8 = const(7)
SDL_PIXELTYPE_ARRAYU16 = const(8)
SDL_PIXELTYPE_ARRAYU32 = const(9)
SDL_PIXELTYPE_ARRAYF16 = const(10)
SDL_PIXELTYPE_ARRAYF32 = const(11)

# SDL_PACKEDORDER values
SDL_PACKEDORDER_NONE = const(0)
SDL_PACKEDORDER_XRGB = const(1)
SDL_PACKEDORDER_RGBX = const(2)
SDL_PACKEDORDER_ARGB = const(3)
SDL_PACKEDORDER_RGBA = const(4)
SDL_PACKEDORDER_XBGR = const(5)
SDL_PACKEDORDER_BGRX = const(6)
SDL_PACKEDORDER_ABGR = const(7)
SDL_PACKEDORDER_BGRA = const(8)

# SDL_ARRAYORDER values
SDL_ARRAYORDER_NONE = const(0)
SDL_ARRAYORDER_RGB = const(1)
SDL_ARRAYORDER_RGBA = const(2)
SDL_ARRAYORDER_ARGB = const(3)
SDL_ARRAYORDER_BGR = const(4)
SDL_ARRAYORDER_BGRA = const(5)
SDL_ARRAYORDER_ABGR = const(6)

# SDL_PACKEDLAYOUT values
SDL_PACKEDLAYOUT_NONE = const(0)
SDL_PACKEDLAYOUT_332 = const(1)
SDL_PACKEDLAYOUT_4444 = const(2)
SDL_PACKEDLAYOUT_1555 = const(3)
SDL_PACKEDLAYOUT_5551 = const(4)
SDL_PACKEDLAYOUT_565 = const(5)
SDL_PACKEDLAYOUT_8888 = const(6)
SDL_PACKEDLAYOUT_2101010 = const(7)
SDL_PACKEDLAYOUT_1010102 = const(8)

# SDL_BITMAPORDER values
SDL_BITMAPORDER_NONE = const(0)
SDL_BITMAPORDER_4321 = const(1)
SDL_BITMAPORDER_1234 = const(2)

# SDL_PIXELFORMAT values
SDL_PIXELFORMAT_UNKNOWN = const(0)
SDL_PIXELFORMAT_INDEX1LSB = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_INDEX1, SDL_BITMAPORDER_4321, 0, 1, 0
)
SDL_PIXELFORMAT_INDEX1MSB = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_INDEX1, SDL_BITMAPORDER_1234, 0, 1, 0
)
SDL_PIXELFORMAT_INDEX4LSB = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_INDEX4, SDL_BITMAPORDER_4321, 0, 4, 0
)
SDL_PIXELFORMAT_INDEX4MSB = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_INDEX4, SDL_BITMAPORDER_1234, 0, 4, 0
)
SDL_PIXELFORMAT_INDEX8 = SDL_DEFINE_PIXELFORMAT(SDL_PIXELTYPE_INDEX8, 0, 0, 8, 1)
SDL_PIXELFORMAT_RGB332 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED8, SDL_PACKEDORDER_XRGB, SDL_PACKEDLAYOUT_332, 8, 1
)
SDL_PIXELFORMAT_XRGB4444 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XRGB, SDL_PACKEDLAYOUT_4444, 12, 2
)
SDL_PIXELFORMAT_RGB444 = SDL_PIXELFORMAT_XRGB4444
SDL_PIXELFORMAT_XBGR4444 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XBGR, SDL_PACKEDLAYOUT_4444, 12, 2
)
SDL_PIXELFORMAT_BGR444 = SDL_PIXELFORMAT_XBGR4444
SDL_PIXELFORMAT_XRGB1555 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XRGB, SDL_PACKEDLAYOUT_1555, 15, 2
)
SDL_PIXELFORMAT_RGB555 = SDL_PIXELFORMAT_XRGB1555
SDL_PIXELFORMAT_XBGR1555 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XBGR, SDL_PACKEDLAYOUT_1555, 15, 2
)
SDL_PIXELFORMAT_BGR555 = SDL_PIXELFORMAT_XBGR1555
SDL_PIXELFORMAT_ARGB4444 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_ARGB, SDL_PACKEDLAYOUT_4444, 16, 2
)
SDL_PIXELFORMAT_RGBA4444 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_RGBA, SDL_PACKEDLAYOUT_4444, 16, 2
)
SDL_PIXELFORMAT_ABGR4444 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_ABGR, SDL_PACKEDLAYOUT_4444, 16, 2
)
SDL_PIXELFORMAT_BGRA4444 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_BGRA, SDL_PACKEDLAYOUT_4444, 16, 2
)
SDL_PIXELFORMAT_ARGB1555 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_ARGB, SDL_PACKEDLAYOUT_1555, 16, 2
)
SDL_PIXELFORMAT_RGBA5551 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_RGBA, SDL_PACKEDLAYOUT_5551, 16, 2
)
SDL_PIXELFORMAT_ABGR1555 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_ABGR, SDL_PACKEDLAYOUT_1555, 16, 2
)
SDL_PIXELFORMAT_BGRA5551 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_BGRA, SDL_PACKEDLAYOUT_5551, 16, 2
)
SDL_PIXELFORMAT_RGB565 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XRGB, SDL_PACKEDLAYOUT_565, 16, 2
)
SDL_PIXELFORMAT_BGR565 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XBGR, SDL_PACKEDLAYOUT_565, 16, 2
)
SDL_PIXELFORMAT_RGB24 = SDL_DEFINE_PIXELFORMAT(SDL_PIXELTYPE_ARRAYU8, SDL_ARRAYORDER_RGB, 0, 24, 3)
SDL_PIXELFORMAT_BGR24 = SDL_DEFINE_PIXELFORMAT(SDL_PIXELTYPE_ARRAYU8, SDL_ARRAYORDER_BGR, 0, 24, 3)
SDL_PIXELFORMAT_XRGB8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_XRGB, SDL_PACKEDLAYOUT_8888, 24, 4
)
SDL_PIXELFORMAT_RGB888 = SDL_PIXELFORMAT_XRGB8888
SDL_PIXELFORMAT_RGBX8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_RGBX, SDL_PACKEDLAYOUT_8888, 24, 4
)
SDL_PIXELFORMAT_XBGR8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_XBGR, SDL_PACKEDLAYOUT_8888, 24, 4
)
SDL_PIXELFORMAT_BGR888 = SDL_PIXELFORMAT_XBGR8888
SDL_PIXELFORMAT_BGRX8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_BGRX, SDL_PACKEDLAYOUT_8888, 24, 4
)
SDL_PIXELFORMAT_ARGB8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_ARGB, SDL_PACKEDLAYOUT_8888, 32, 4
)
SDL_PIXELFORMAT_RGBA8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_RGBA, SDL_PACKEDLAYOUT_8888, 32, 4
)
SDL_PIXELFORMAT_ABGR8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_ABGR, SDL_PACKEDLAYOUT_8888, 32, 4
)
SDL_PIXELFORMAT_BGRA8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_BGRA, SDL_PACKEDLAYOUT_8888, 32, 4
)
SDL_PIXELFORMAT_ARGB2101010 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_ARGB, SDL_PACKEDLAYOUT_2101010, 32, 4
)

_USE_FFI = False
if sys.implementation.name == "micropython" and sys.platform != "win32":
    try:
        import ffi  # noqa: F401
        import uctypes  # noqa: F401

        _USE_FFI = True
    except ImportError:
        pass

_FFI_FUNCS = (
    ("SDL_Init", "i", "I"),
    ("SDL_InitSubSystem", "i", "I"),
    ("SDL_Quit", "v", ""),
    ("SDL_GetError", "s", ""),
    ("SDL_PollEvent", "i", "P"),
    ("SDL_NumJoysticks", "i", ""),
    ("SDL_JoystickOpen", "P", "i"),
    ("SDL_JoystickClose", "v", "P"),
    ("SDL_JoystickInstanceID", "i", "P"),
    ("SDL_GetKeyName", "s", "i"),
    ("SDL_GetKeyFromName", "i", "s"),
    ("SDL_CreateWindow", "P", "siiiii"),
    ("SDL_DestroyWindow", "v", "P"),
    ("SDL_SetWindowSize", "v", "Pii"),
    ("SDL_CreateRenderer", "P", "PiI"),
    ("SDL_DestroyRenderer", "v", "P"),
    ("SDL_SetRenderDrawColor", "i", "PPPP"),
    ("SDL_SetRenderTarget", "i", "pP"),
    ("SDL_RenderClear", "v", "P"),
    ("SDL_RenderCopy", "v", "PPPP"),
    ("SDL_RenderCopyEx", "v", "PPPPdPPi"),
    ("SDL_RenderPresent", "v", "P"),
    ("SDL_RenderFillRect", "i", "PP"),
    ("SDL_RenderSetLogicalSize", "i", "Pii"),
    ("SDL_CreateTexture", "P", "PIiiii"),
    ("SDL_DestroyTexture", "v", "P"),
    ("SDL_SetTextureBlendMode", "i", "PI"),
    ("SDL_UpdateTexture", "i", "PPPi"),
    ("SDL_AddTimer", "P", "IPP"),
    ("SDL_RemoveTimer", "i", "P"),
    ("SDL_GetDisplayUsableBounds", "i", "iP"),
    ("SDL_GetDesktopDisplayMode", "i", "iP"),
)


def _bind_ffi(lib, specs):
    for name, ret, args in specs:
        globals()[name] = lib.func(ret, name, args)


def _bind_ctypes(lib, specs):
    for name, restype, argtypes in specs:
        fn = getattr(lib, name)
        fn.restype = restype
        fn.argtypes = list(argtypes)
        globals()[name] = fn


if _USE_FFI:
    import struct

    import ffi
    import uctypes

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

    _bind_ffi(_libSDL2, _FFI_FUNCS)

    def SDL_TimerCallback(tcb):
        return ffi.callback("I", tcb, "IP")

else:
    import ctypes

    if sys.platform == "win32":
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

    class SDL_DisplayMode(ctypes.Structure):
        _fields_ = [
            ("format", ctypes.c_uint32),
            ("w", ctypes.c_int),
            ("h", ctypes.c_int),
            ("refresh_rate", ctypes.c_int),
            ("driverdata", ctypes.c_void_p),
        ]

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

    _c = ctypes
    _v = _c.c_void_p
    _i = _c.c_int
    _u = _c.c_uint
    _u8 = _c.c_uint8
    _u16 = _c.c_uint16
    _u32 = _c.c_uint32
    _d = _c.c_double
    _f = _c.c_float
    _p = _c.c_char_p
    _r = _c.POINTER(SDL_Rect)
    _dm = _c.POINTER(SDL_DisplayMode)
    _pt = _c.POINTER(SDL_Point)
    _ce = _c.POINTER(SDL_CommonEvent)

    _CTYPES_FUNCS = (
        ("SDL_Init", _i, (_u,)),
        ("SDL_InitSubSystem", _i, (_u,)),
        ("SDL_Quit", None, ()),
        ("SDL_GetError", _p, ()),
        ("SDL_PollEvent", _i, (_ce,)),
        ("SDL_NumJoysticks", _i, ()),
        ("SDL_JoystickOpen", _v, (_i,)),
        ("SDL_JoystickClose", None, (_v,)),
        ("SDL_JoystickInstanceID", _i, (_v,)),
        ("SDL_GetKeyName", _p, (_i,)),
        ("SDL_GetKeyFromName", _i, (_p,)),
        ("SDL_CreateWindow", _v, (_p, _i, _i, _i, _i, _u)),
        ("SDL_DestroyWindow", None, (_v,)),
        ("SDL_SetWindowSize", None, (_v, _i, _i)),
        ("SDL_CreateRenderer", _v, (_v, _i, _u)),
        ("SDL_DestroyRenderer", None, (_v,)),
        ("SDL_SetRenderDrawColor", _i, (_v, _u, _u, _u, _u)),
        ("SDL_SetRenderTarget", _i, (_v, _v)),
        ("SDL_RenderClear", _i, (_v,)),
        ("SDL_RenderCopy", _i, (_v, _v, _r, _r)),
        ("SDL_RenderCopyEx", _i, (_v, _v, _r, _r, _d, _pt, _i)),
        ("SDL_RenderPresent", None, (_v,)),
        ("SDL_RenderFillRect", _i, (_v, _r)),
        ("SDL_RenderSetLogicalSize", _i, (_v, _i, _i)),
        ("SDL_CreateTexture", _v, (_v, _u, _i, _i, _i)),
        ("SDL_DestroyTexture", None, (_v,)),
        ("SDL_SetTextureBlendMode", _i, (_v, _i)),
        ("SDL_UpdateTexture", _i, (_v, _r, _v, _i)),
        ("SDL_AddTimer", _v, (_u32, _v, _v)),
        ("SDL_RemoveTimer", _i, (_v,)),
        ("SDL_GetDisplayUsableBounds", _i, (_i, _r)),
        ("SDL_GetDesktopDisplayMode", _i, (_i, _dm)),
    )
    _bind_ctypes(_libSDL2, _CTYPES_FUNCS)

    SDL_TimerCallback = ctypes.CFUNCTYPE(_u32, _u32, _v)

_EVENT_SIZE = 56

_event_struct_map = {
    SDL_KEYDOWN: SDL_KeyboardEvent,
    SDL_KEYUP: SDL_KeyboardEvent,
    SDL_MOUSEMOTION: SDL_MouseMotionEvent,
    SDL_MOUSEBUTTONDOWN: SDL_MouseButtonEvent,
    SDL_MOUSEBUTTONUP: SDL_MouseButtonEvent,
    SDL_MOUSEWHEEL: SDL_MouseWheelEvent,
    SDL_JOYAXISMOTION: SDL_JoyAxisEvent,
    SDL_JOYBALLMOTION: SDL_JoyBallEvent,
    SDL_JOYHATMOTION: SDL_JoyHatEvent,
    SDL_JOYBUTTONDOWN: SDL_JoyButtonEvent,
    SDL_JOYBUTTONUP: SDL_JoyButtonEvent,
    SDL_POLLSENTINEL: SDL_CommonEvent,
}


def SDL_Event(event=None):
    """Return an SDL_Event buffer or decode *event* to a typed struct."""
    if event is None:
        if _USE_FFI:
            return bytearray(_EVENT_SIZE)
        return SDL_CommonEvent.from_buffer(ctypes.create_string_buffer(_EVENT_SIZE))

    if _USE_FFI:
        event_type = int.from_bytes(event[:4], "little")
        desc = _event_struct_map.get(event_type, SDL_CommonEvent)
        return uctypes.struct(uctypes.addressof(event), desc)

    event_type = event.type
    struct_cls = _event_struct_map.get(event_type, SDL_CommonEvent)
    return struct_cls.from_buffer(event)
