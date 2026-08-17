# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Pure-Python ``usdl2`` fallback: an **SDL2 subset for Python**.

Used when the native C ``usdl2`` module is unavailable. Must stay in lockstep
with the C sources in this repo (see ``src/usdl2_module_globals.inc`` and
``src/usdl2_cpy.c`` / ``src/usdl2_mp.c``).

Hard rule — **SDL2 symbols only**:
  Export only names that exist in SDL2 (``SDL_*`` functions/constants/macros
  and binding constructors for SDL types: ``SDL_Rect``, ``SDL_Point``,
  ``SDL_Event``, ``SDL_TimerCallback``, ``SDL_DEFINE_PIXELFORMAT``, …).
  Do **not** invent helpers such as ``process_exit``, ``pump_scheduler``, a
  bare ``Event`` type, or other non-SDL module attributes. Past agents added
  those for timing/shutdown; put such logic in the *consumer* (e.g.
  ``sdldisplay``, ``multimer``) instead. MP cooperative timer delivery may
  ride inside real SDL entry points (e.g. ``SDL_PumpEvents``) as a private
  implementation detail — never as a new public name.

Public surface matches native usdl2: same ``SDL_*`` API, 56-byte ``SDL_Event``
with the same subviews, ``SDL_Rect``/``SDL_Point`` as packed bytes, timer API
via ``SDL_TimerCallback`` / ``SDL_AddTimer`` / ``SDL_RemoveTimer``. Opaque
handles are plain ints (falsy when 0/NULL).

Lives at ``lib/usdl2.py`` in this repo. Published as TestPyPI ``usdl2-py`` /
MIP ``usdl2`` (same release tag as the native ``usdl2`` wheels). Uses
**ctypes** on CPython (unix and win32); **ffi** on MicroPython unix.
"""

import struct
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
# SDL_HINT_ORIENTATIONS — space-delimited LandscapeLeft/Right Portrait…
SDL_HINT_ORIENTATIONS = "SDL_IOS_ORIENTATIONS"
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

# SDL_AudioFormat values
AUDIO_U8 = const(0x0008)
AUDIO_S8 = const(0x8008)
AUDIO_U16LSB = const(0x0010)
AUDIO_S16LSB = const(0x8010)
AUDIO_U16MSB = const(0x1010)
AUDIO_S16MSB = const(0x9010)
AUDIO_S32LSB = const(0x8020)
AUDIO_S32MSB = const(0x9020)
AUDIO_F32LSB = const(0x8120)
AUDIO_F32MSB = const(0x9120)
if sys.byteorder == "little":
    AUDIO_U16SYS = AUDIO_U16LSB
    AUDIO_S16SYS = AUDIO_S16LSB
    AUDIO_S32SYS = AUDIO_S32LSB
    AUDIO_F32SYS = AUDIO_F32LSB
else:
    AUDIO_U16SYS = AUDIO_U16MSB
    AUDIO_S16SYS = AUDIO_S16MSB
    AUDIO_S32SYS = AUDIO_S32MSB
    AUDIO_F32SYS = AUDIO_F32MSB

# SDL_Texture values
SDL_TEXTUREACCESS_STATIC = const(0)
SDL_TEXTUREACCESS_STREAMING = const(1)
SDL_TEXTUREACCESS_TARGET = const(2)

# SDL_BlendMode values
SDL_BLENDMODE_NONE = const(1)
SDL_BLENDMODE_BLEND = const(2)
SDL_BLENDMODE_ADD = const(3)
SDL_BLENDMODE_MOD = const(4)

# SDL_Event types (not complete)
SDL_QUIT = const(0x100)  # User-requested quit
SDL_WINDOWEVENT = const(0x200)  # Window state change
SDL_WINDOWEVENT_CLOSE = const(0xE)  # Window close requested
SDL_KEYDOWN = const(0x300)  # Key pressed
SDL_KEYUP = const(0x301)  # Key released
SDL_MOUSEMOTION = const(0x400)  # Mouse moved
SDL_MOUSEBUTTONDOWN = const(0x401)  # Mouse button pressed
SDL_MOUSEBUTTONUP = const(0x402)  # Mouse button released
SDL_MOUSEWHEEL = const(0x403)  # Mouse wheel motion
SDL_FINGERDOWN = const(0x700)  # Finger touched
SDL_FINGERUP = const(0x701)  # Finger lifted
SDL_FINGERMOTION = const(0x702)  # Finger moved
SDL_JOYAXISMOTION = const(0x600)  # Joystick axis motion
SDL_JOYBALLMOTION = const(0x601)  # Joystick trackball motion
SDL_JOYHATMOTION = const(0x602)  # Joystick hat position change
SDL_JOYBUTTONDOWN = const(0x603)  # Joystick button pressed
SDL_JOYBUTTONUP = const(0x604)  # Joystick button released
SDL_JOYDEVICEADDED = const(0x605)  # A joystick was connected
SDL_JOYDEVICEREMOVED = const(0x606)  # A joystick was disconnected

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
SDL_PIXELFORMAT_RGB444 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XRGB, SDL_PACKEDLAYOUT_4444, 12, 2
)
SDL_PIXELFORMAT_RGB555 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XRGB, SDL_PACKEDLAYOUT_1555, 15, 2
)
SDL_PIXELFORMAT_BGR555 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED16, SDL_PACKEDORDER_XBGR, SDL_PACKEDLAYOUT_1555, 15, 2
)
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
SDL_PIXELFORMAT_RGB888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_XRGB, SDL_PACKEDLAYOUT_8888, 24, 4
)
SDL_PIXELFORMAT_RGBX8888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_RGBX, SDL_PACKEDLAYOUT_8888, 24, 4
)
SDL_PIXELFORMAT_BGR888 = SDL_DEFINE_PIXELFORMAT(
    SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_XBGR, SDL_PACKEDLAYOUT_8888, 24, 4
)
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


###############################################################################
#                          SDL_Rect / SDL_Point                               #
###############################################################################

# Packed as bytes (not a ctypes.Structure / uctypes struct) so the same value
# is usable, unmodified, on every backend -- matches py_SDL_Rect()/py_SDL_Point()
# in usdl2_cpy.c, which pack a bytes object directly.


def SDL_Rect(x=0, y=0, w=0, h=0):
    return struct.pack("<iiii", x, y, w, h)


def SDL_Point(x=0, y=0):
    return struct.pack("<ii", x, y)


def SDL_AudioSpec(freq=0, format=0, channels=0, samples=0):
    """Return a packed SDL_AudioSpec with a NULL callback for queued audio."""
    return bytearray(
        struct.pack(
            "@iHBBHHIPP",
            freq,
            format,
            channels,
            0,
            samples,
            0,
            0,
            0,
            0,
        )
    )


###############################################################################
#                          SDL_Event / subviews                               #
###############################################################################

_EVENT_SIZE = const(56)


def _is_joystick_event(event_type):
    return SDL_JOYAXISMOTION <= event_type <= SDL_JOYDEVICEREMOVED


def _u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def _i32(data, off):
    return struct.unpack_from("<i", data, off)[0]


def _i16(data, off):
    return struct.unpack_from("<h", data, off)[0]


def _f32(data, off):
    return struct.unpack_from("<f", data, off)[0]


def _i64(data, off):
    return struct.unpack_from("<q", data, off)[0]


def _is_finger_event(event_type):
    return event_type in (SDL_FINGERDOWN, SDL_FINGERUP, SDL_FINGERMOTION)


class _SubView:
    """
    A view into an SDL_Event's 8-byte-aligned union payload.

    Mirrors the ``_SubView``/subview getters in usdl2_cpy.c: ``motion``,
    ``key``, ``button``, ``wheel``, ``jaxis``, ``jball``, ``jhat`` and
    ``jbutton`` all view the same union at offset 8 (immediately after
    ``type``+``timestamp``), matching the real ``SDL_Event`` layout.
    """

    def __init__(self, event, base):
        self._event = event
        self._base = base

    @property
    def windowID(self):
        data = self._event._data
        if _is_finger_event(_u32(data, 0)):
            return _u32(data, self._base + 36)
        return _u32(data, self._base + 0)

    @property
    def which(self):
        data = self._event._data
        event_type = _u32(data, 0)
        if _is_joystick_event(event_type):
            return _i32(data, self._base + 0)
        return _u32(data, self._base + 4)

    @property
    def touchId(self):
        return _i64(self._event._data, self._base + 0)

    @property
    def fingerId(self):
        return _i64(self._event._data, self._base + 8)

    @property
    def state(self):
        data = self._event._data
        event_type = _u32(data, 0)
        if self._base == 8 and event_type == SDL_MOUSEMOTION:
            return _u32(data, self._base + 8)
        if event_type in (SDL_JOYBUTTONDOWN, SDL_JOYBUTTONUP):
            return data[self._base + 5]
        return data[self._base + 4]

    @property
    def x(self):
        data = self._event._data
        if _is_finger_event(_u32(data, 0)):
            return _f32(data, self._base + 16)
        return _i32(data, self._base + 12)

    @property
    def y(self):
        data = self._event._data
        if _is_finger_event(_u32(data, 0)):
            return _f32(data, self._base + 20)
        return _i32(data, self._base + 16)

    @property
    def dx(self):
        return _f32(self._event._data, self._base + 24)

    @property
    def dy(self):
        return _f32(self._event._data, self._base + 28)

    @property
    def pressure(self):
        return _f32(self._event._data, self._base + 32)

    @property
    def xrel(self):
        data = self._event._data
        if _u32(data, 0) == SDL_JOYBALLMOTION:
            return _i16(data, self._base + 8)
        return _i32(data, self._base + 20)

    @property
    def yrel(self):
        data = self._event._data
        if _u32(data, 0) == SDL_JOYBALLMOTION:
            return _i16(data, self._base + 10)
        return _i32(data, self._base + 24)

    @property
    def button(self):
        data = self._event._data
        event_type = _u32(data, 0)
        if event_type in (SDL_JOYBUTTONDOWN, SDL_JOYBUTTONUP):
            return data[self._base + 4]
        return data[self._base + 8]

    @property
    def clicks(self):
        return self._event._data[self._base + 10]

    @property
    def direction(self):
        return _u32(self._event._data, self._base + 16)

    @property
    def preciseX(self):
        return _f32(self._event._data, self._base + 0)

    @property
    def preciseY(self):
        return _f32(self._event._data, self._base + 4)

    @property
    def repeat(self):
        return self._event._data[self._base + 5]

    @property
    def keysym(self):
        return _SubView(self._event, self._base + 8)

    @property
    def scancode(self):
        return _i32(self._event._data, self._base + 0)

    @property
    def sym(self):
        return _i32(self._event._data, self._base + 4)

    @property
    def mod(self):
        return _u32(self._event._data, self._base + 8) & 0xFFFF

    @property
    def axis(self):
        return self._event._data[self._base + 4]

    @property
    def value(self):
        data = self._event._data
        event_type = _u32(data, 0)
        if event_type == SDL_JOYAXISMOTION:
            return _i16(data, self._base + 8)
        if event_type == SDL_JOYHATMOTION:
            return data[self._base + 5]
        raise AttributeError("value")

    @property
    def ball(self):
        return self._event._data[self._base + 4]

    @property
    def hat(self):
        return self._event._data[self._base + 4]

    @property
    def event(self):
        """SDL_WindowEvent.event (Uint8) at union+4."""
        return self._event._data[self._base + 4]


class SDL_Event:
    """
    56-byte SDL_Event buffer, mirroring ``usdl2.SDL_Event`` in the native module.

    * ``SDL_Event()`` / ``SDL_Event(None)`` -> a new zero-filled event.
    * ``SDL_Event(<bytes-like>)`` -> a new event, copied from the buffer.
    * ``SDL_Event(<existing SDL_Event>)`` -> the same instance (identity).
    """

    def __new__(cls, event=None):
        if isinstance(event, cls):
            return event
        self = super().__new__(cls)
        if event is None:
            self._data = bytearray(_EVENT_SIZE)
        else:
            buf = memoryview(event)
            if len(buf) < _EVENT_SIZE:
                raise ValueError("event buffer too small")
            self._data = bytearray(buf[:_EVENT_SIZE])
        return self

    def __len__(self):
        return _EVENT_SIZE

    @property
    def type(self):
        return _u32(self._data, 0)

    @type.setter
    def type(self, value):
        struct.pack_into("<I", self._data, 0, value)

    @property
    def timestamp(self):
        return _u32(self._data, 4)

    @property
    def motion(self):
        return _SubView(self, 8)

    key = motion
    button = motion
    wheel = motion
    jaxis = motion
    jball = motion
    jhat = motion
    jbutton = motion
    tfinger = motion
    window = motion


###############################################################################
#                          Backend loader                                     #
###############################################################################

_use_ffi = False
if sys.implementation.name == "micropython" and sys.platform != "win32":
    try:
        import ffi  # noqa: F401

        _use_ffi = True
    except ImportError:
        pass

# (name, return type, arg types) using modffi's struct-like type codes; see
# MicroPython ports/unix/modffi.c. Buffer-taking functions (SDL_PollEvent,
# SDL_UpdateTexture, SDL_RenderReadPixels, SDL_GetDisplayUsableBounds,
# SDL_GetDesktopDisplayMode) are bound under a private name and wrapped below
# so callers can pass an SDL_Event or any bytes-like object directly, matching
# usdl2_cpy.c's PyObject_GetBuffer() flexibility.
_FFI_FUNCS = (
    ("SDL_Init", "i", "I"),
    ("SDL_InitSubSystem", "i", "I"),
    ("SDL_Quit", "v", ""),
    # _raw_* names: wrapped below for NULL/str encoding parity with usdl2_cpy.c
    ("_raw_SDL_GetError", "s", ""),
    ("_raw_SDL_SetHint", "i", "ss"),
    ("SDL_CreateWindow", "P", "siiiii"),
    ("SDL_DestroyWindow", "v", "P"),
    ("SDL_GetWindowID", "I", "P"),
    ("SDL_SetWindowSize", "v", "Pii"),
    ("SDL_SetWindowResizable", "v", "Pi"),
    ("SDL_SetWindowMinimumSize", "v", "Pii"),
    ("SDL_SetWindowMaximumSize", "v", "Pii"),
    ("SDL_CreateRenderer", "P", "PiI"),
    ("SDL_DestroyRenderer", "v", "P"),
    ("SDL_SetRenderDrawColor", "i", "PIIII"),
    ("SDL_SetRenderTarget", "i", "PP"),
    ("SDL_RenderClear", "v", "P"),
    ("SDL_RenderCopy", "v", "PPPP"),
    ("SDL_RenderCopyEx", "v", "PPPPdPi"),
    ("_lib_SDL_RenderReadPixels", "i", "PPIPi"),
    ("SDL_RenderPresent", "v", "P"),
    ("SDL_RenderFillRect", "i", "PP"),
    ("SDL_RenderSetLogicalSize", "i", "Pii"),
    ("SDL_CreateTexture", "P", "PIiii"),
    ("SDL_DestroyTexture", "v", "P"),
    ("SDL_SetTextureBlendMode", "i", "Pi"),
    ("SDL_NumJoysticks", "i", ""),
    ("SDL_JoystickOpen", "P", "i"),
    ("SDL_JoystickClose", "v", "P"),
    ("SDL_JoystickInstanceID", "i", "P"),
    ("_raw_SDL_GetKeyName", "s", "i"),
    ("_lib_SDL_PumpEvents", "v", ""),
    ("_lib_SDL_PollEvent", "i", "P"),
    ("_lib_SDL_UpdateTexture", "i", "PPPi"),
    ("_lib_SDL_GetDisplayUsableBounds", "i", "iP"),
    ("_lib_SDL_GetDesktopDisplayMode", "i", "iP"),
    ("SDL_GetNumAudioDevices", "i", "i"),
    ("_raw_SDL_GetAudioDeviceName", "s", "ii"),
    ("_lib_SDL_OpenAudioDevice", "I", "siPPi"),
    ("SDL_CloseAudioDevice", "v", "I"),
    ("SDL_PauseAudioDevice", "v", "Ii"),
    ("_lib_SDL_QueueAudio", "i", "IPI"),
    ("_lib_SDL_DequeueAudio", "I", "IPI"),
    ("SDL_GetQueuedAudioSize", "I", "I"),
    ("SDL_ClearQueuedAudio", "v", "I"),
    ("SDL_LockAudioDevice", "v", "I"),
    ("SDL_UnlockAudioDevice", "v", "I"),
    # No real SDL_AddTimer/SDL_RemoveTimer binding here -- see the "Timer API"
    # section: SDL's timer thread is never registered with the MicroPython
    # runtime (mp_thread_init()), and calling back into the interpreter from
    # it segfaults unconditionally (verified experimentally), so MicroPython
    # timers are cooperative/software instead of real SDL ones.
)


def _libsym(name):
    """C symbol name for a (possibly privately-named) binding, e.g.
    "_lib_SDL_PollEvent" / "_raw_SDL_GetError" -> "SDL_PollEvent" / "SDL_GetError"."""
    if name.startswith("_lib_") or name.startswith("_raw_"):
        return name[5:]
    return name


def _bind_ffi(lib, specs):
    for name, ret, args in specs:
        globals()[name] = lib.func(ret, _libsym(name), args)


def _bind_ctypes(lib, specs):
    for name, restype, argtypes in specs:
        fn = getattr(lib, _libsym(name))
        fn.restype = restype
        fn.argtypes = list(argtypes)
        globals()[name] = fn


if _use_ffi:
    _libSDL2 = ffi.open("libSDL2-2.0.so.0")
    _bind_ffi(_libSDL2, _FFI_FUNCS)
    _raw_SDL_GetError = globals()["_raw_SDL_GetError"]
    _raw_SDL_GetKeyName = globals()["_raw_SDL_GetKeyName"]
    _raw_SDL_SetHint = globals()["_raw_SDL_SetHint"]

    def _wrap_buf(buf, writable=False):
        return buf

    # modffi's "s" return type yields None for a NULL C string; SDL never
    # actually returns NULL for either of these, but fall back to "" to
    # match usdl2_cpy.c's PyUnicode_FromString(err ? err : "") exactly.
    def SDL_GetError():
        err = _raw_SDL_GetError()
        return err if err is not None else ""

    def SDL_GetKeyName(sym):
        name = _raw_SDL_GetKeyName(sym)
        return name if name is not None else ""

    def SDL_SetHint(name, value):
        if isinstance(name, str):
            name = name.encode("utf-8")
        if isinstance(value, str):
            value = value.encode("utf-8")
        return _raw_SDL_SetHint(name, value)

else:
    import ctypes

    def _load_sdl2():
        if sys.platform == "win32":
            return ctypes.CDLL("SDL2.dll")
        # Desktop SONAME first; p4a / Android APKs typically expose libSDL2.so.
        names = ("libSDL2-2.0.so.0", "libSDL2.so")
        if sys.platform == "android":
            names = ("libSDL2.so", "libSDL2-2.0.so.0")
        errors = []
        for name in names:
            try:
                return ctypes.CDLL(name)
            except OSError as exc:
                errors.append("{}: {}".format(name, exc))
        raise OSError(
            "Could not load SDL2 library; tried: {}".format("; ".join(errors))
        )

    _libSDL2 = _load_sdl2()

    _c = ctypes
    _v = _c.c_void_p
    _i = _c.c_int
    _u = _c.c_uint
    _d = _c.c_double

    # Rect/Point/Event/DisplayMode arguments are all c_void_p: SDL_Rect()/
    # SDL_Point() return plain bytes (accepted directly by ctypes for a
    # c_void_p argument), and _wrap_buf() below adapts other buffer-protocol
    # objects the same way usdl2_cpy.c's PyObject_GetBuffer() does
    # (PyBUF_SIMPLE vs PyBUF_WRITABLE via the writable= flag).
    _CTYPES_FUNCS = (
        ("SDL_Init", _i, (_u,)),
        ("SDL_InitSubSystem", _i, (_u,)),
        ("SDL_Quit", None, ()),
        ("_raw_SDL_GetError", _c.c_char_p, ()),
        ("_raw_SDL_SetHint", _i, (_c.c_char_p, _c.c_char_p)),
        ("_raw_SDL_CreateWindow", _v, (_c.c_char_p, _i, _i, _i, _i, _u)),
        ("SDL_DestroyWindow", None, (_v,)),
        ("SDL_GetWindowID", _u, (_v,)),
        ("SDL_SetWindowSize", None, (_v, _i, _i)),
        ("SDL_SetWindowResizable", None, (_v, _i)),
        ("SDL_SetWindowMinimumSize", None, (_v, _i, _i)),
        ("SDL_SetWindowMaximumSize", None, (_v, _i, _i)),
        ("SDL_CreateRenderer", _v, (_v, _i, _u)),
        ("SDL_DestroyRenderer", None, (_v,)),
        ("SDL_SetRenderDrawColor", _i, (_v, _u, _u, _u, _u)),
        ("SDL_SetRenderTarget", _i, (_v, _v)),
        ("SDL_RenderClear", _i, (_v,)),
        ("SDL_RenderCopy", _i, (_v, _v, _v, _v)),
        ("SDL_RenderCopyEx", _i, (_v, _v, _v, _v, _d, _v, _i)),
        ("_lib_SDL_RenderReadPixels", _i, (_v, _v, _u, _v, _i)),
        ("SDL_RenderPresent", None, (_v,)),
        ("SDL_RenderFillRect", _i, (_v, _v)),
        ("SDL_RenderSetLogicalSize", _i, (_v, _i, _i)),
        ("SDL_CreateTexture", _v, (_v, _u, _i, _i, _i)),
        ("SDL_DestroyTexture", None, (_v,)),
        ("SDL_SetTextureBlendMode", _i, (_v, _i)),
        ("SDL_NumJoysticks", _i, ()),
        ("SDL_JoystickOpen", _v, (_i,)),
        ("SDL_JoystickClose", None, (_v,)),
        ("SDL_JoystickInstanceID", _i, (_v,)),
        ("_raw_SDL_GetKeyName", _c.c_char_p, (_i,)),
        ("_lib_SDL_PumpEvents", None, ()),
        ("_lib_SDL_PollEvent", _i, (_v,)),
        ("_lib_SDL_UpdateTexture", _i, (_v, _v, _v, _i)),
        ("_lib_SDL_GetDisplayUsableBounds", _i, (_i, _v)),
        ("_lib_SDL_GetDesktopDisplayMode", _i, (_i, _v)),
        ("SDL_GetNumAudioDevices", _i, (_i,)),
        ("_raw_SDL_GetAudioDeviceName", _c.c_char_p, (_i, _i)),
        ("_lib_SDL_OpenAudioDevice", _u, (_c.c_char_p, _i, _v, _v, _i)),
        ("SDL_CloseAudioDevice", None, (_u,)),
        ("SDL_PauseAudioDevice", None, (_u, _i)),
        ("_lib_SDL_QueueAudio", _i, (_u, _v, _u)),
        ("_lib_SDL_DequeueAudio", _u, (_u, _v, _u)),
        ("SDL_GetQueuedAudioSize", _u, (_u,)),
        ("SDL_ClearQueuedAudio", None, (_u,)),
        ("SDL_LockAudioDevice", None, (_u,)),
        ("SDL_UnlockAudioDevice", None, (_u,)),
        # SDL_AddTimer/SDL_RemoveTimer are bound separately below (need the
        # timer trampoline's CFUNCTYPE to exist first).
    )
    _bind_ctypes(_libSDL2, _CTYPES_FUNCS)
    _raw_SDL_GetError = globals()["_raw_SDL_GetError"]
    _raw_SDL_GetKeyName = globals()["_raw_SDL_GetKeyName"]
    _raw_SDL_SetHint = globals()["_raw_SDL_SetHint"]
    _raw_SDL_CreateWindow = globals()["_raw_SDL_CreateWindow"]

    def _wrap_buf(buf, writable=False):
        """Adapt a bytes-like object for a ctypes c_void_p argument.

        Mirrors usdl2_cpy.c: ``writable=False`` is PyBUF_SIMPLE (QueueAudio,
        UpdateTexture pixels, …); ``writable=True`` is PyBUF_WRITABLE
        (DequeueAudio, PollEvent, out-params, …).

        Immutable ``bytes`` convert directly for read-only use. Writable
        buffers use ``from_buffer`` so the callee can mutate in place.
        Readonly memoryviews (e.g. ``memoryview(b\"...\")`` from audiodev)
        use ``from_buffer_copy`` under PyBUF_SIMPLE — ``from_buffer`` rejects
        them with TypeError.
        """
        if buf is None or isinstance(buf, (int, ctypes.Array)):
            return buf
        if isinstance(buf, bytes):
            if writable:
                raise TypeError("underlying buffer is not writable")
            return buf
        arr_type = ctypes.c_char * len(buf)
        if writable:
            return arr_type.from_buffer(buf)
        try:
            return arr_type.from_buffer(buf)
        except TypeError:
            return arr_type.from_buffer_copy(buf)

    # SDL_GetError()/SDL_GetKeyName() use c_char_p (not modelled as "P" in the
    # ffi table above) so ctypes decodes the returned C string for us; wrap
    # them to fall back to "" for NULL, matching usdl2_cpy.c.
    def SDL_GetError():
        err = _raw_SDL_GetError()
        return err.decode("utf-8") if err else ""

    def SDL_GetKeyName(sym):
        name = _raw_SDL_GetKeyName(sym)
        return name.decode("utf-8") if name else ""

    def SDL_CreateWindow(title, x, y, w, h, flags):
        if isinstance(title, str):
            title = title.encode("utf-8")
        return _raw_SDL_CreateWindow(title, x, y, w, h, flags)

    def SDL_SetHint(name, value):
        if isinstance(name, str):
            name = name.encode("utf-8")
        if isinstance(value, str):
            value = value.encode("utf-8")
        return _raw_SDL_SetHint(name, value)

    _lib_SDL_GetWindowSize = _libSDL2.SDL_GetWindowSize
    _lib_SDL_GetWindowSize.argtypes = (_v, _c.POINTER(_i), _c.POINTER(_i))
    _lib_SDL_GetWindowSize.restype = None
    _lib_SDL_GetRendererOutputSize = _libSDL2.SDL_GetRendererOutputSize
    _lib_SDL_GetRendererOutputSize.argtypes = (_v, _c.POINTER(_i), _c.POINTER(_i))
    _lib_SDL_GetRendererOutputSize.restype = _i

    def SDL_GetWindowSize(window):
        w = _i()
        h = _i()
        _lib_SDL_GetWindowSize(window, _c.byref(w), _c.byref(h))
        return int(w.value), int(h.value)

    def SDL_GetRendererOutputSize(renderer):
        w = _i()
        h = _i()
        if _lib_SDL_GetRendererOutputSize(renderer, _c.byref(w), _c.byref(h)):
            raise RuntimeError(SDL_GetError())
        return int(w.value), int(h.value)


# _bind_ffi / _bind_ctypes assign these via globals()[name]; materialize so
# static analysis and the buffer wrappers below see real module bindings.
_lib_SDL_PumpEvents = globals()["_lib_SDL_PumpEvents"]
_lib_SDL_PollEvent = globals()["_lib_SDL_PollEvent"]
_lib_SDL_UpdateTexture = globals()["_lib_SDL_UpdateTexture"]
_lib_SDL_RenderReadPixels = globals()["_lib_SDL_RenderReadPixels"]
_lib_SDL_GetDisplayUsableBounds = globals()["_lib_SDL_GetDisplayUsableBounds"]
_lib_SDL_GetDesktopDisplayMode = globals()["_lib_SDL_GetDesktopDisplayMode"]
_raw_SDL_GetAudioDeviceName = globals()["_raw_SDL_GetAudioDeviceName"]
_lib_SDL_OpenAudioDevice = globals()["_lib_SDL_OpenAudioDevice"]
_lib_SDL_QueueAudio = globals()["_lib_SDL_QueueAudio"]
_lib_SDL_DequeueAudio = globals()["_lib_SDL_DequeueAudio"]


def SDL_GetAudioDeviceName(index, iscapture):
    name = _raw_SDL_GetAudioDeviceName(index, iscapture)
    if name is None:
        return None
    if isinstance(name, bytes):
        return name.decode("utf-8")
    return name


def SDL_OpenAudioDevice(device, iscapture, desired, obtained, allowed_changes):
    if isinstance(device, str):
        device = device.encode("utf-8")
    return _lib_SDL_OpenAudioDevice(
        device,
        iscapture,
        _wrap_buf(desired),
        _wrap_buf(obtained, writable=True),
        allowed_changes,
    )


def SDL_QueueAudio(device, data, length):
    return _lib_SDL_QueueAudio(device, _wrap_buf(data), length)


def SDL_DequeueAudio(device, data, length):
    return _lib_SDL_DequeueAudio(device, _wrap_buf(data, writable=True), length)


###############################################################################
#                          Timer API                                          #
###############################################################################


class _TimerCallback:
    """Opaque token returned by SDL_TimerCallback(); only usable via SDL_AddTimer()."""

    __slots__ = ("callback",)

    def __init__(self, callback):
        if not callable(callback):
            raise TypeError("callback must be callable")
        self.callback = callback


def SDL_TimerCallback(callback):
    return _TimerCallback(callback)


if _use_ffi:
    # Real SDL timers fire on an SDL-owned pthread that MicroPython's runtime
    # never registered (mp_thread_init() was never called for it); invoking
    # any Python callback from that thread segfaults unconditionally --
    # verified experimentally, even a trivial ffi.callback(..., lock=True)
    # trampoline crashes the moment SDL's timer thread calls it. So on
    # MicroPython, timers are cooperative/software instead of real SDL ones:
    # SDL_AddTimer() just records a deadline, and SDL_PumpEvents()/
    # SDL_PollEvent() -- already polled regularly by the application's event loop,
    # on a safe/registered thread -- fire any due callbacks in-line.
    import time

    _sw_timers = {}
    _sw_timer_next_id = [1]

    def _sw_timers_poll():
        if not _sw_timers:
            return
        now = time.ticks_ms()
        for timer_id, entry in list(_sw_timers.items()):
            deadline, interval, callback, user_param = entry
            if time.ticks_diff(now, deadline) < 0:
                continue
            if timer_id not in _sw_timers:
                continue
            _sw_timers[timer_id] = (
                time.ticks_add(deadline, interval),
                interval,
                callback,
                user_param,
            )
            try:
                callback(interval, user_param)
            except Exception:
                pass

    def SDL_AddTimer(interval, tcb, user_param):
        if not isinstance(tcb, _TimerCallback):
            raise TypeError("callback must be from SDL_TimerCallback()")
        timer_id = _sw_timer_next_id[0]
        _sw_timer_next_id[0] += 1
        _sw_timers[timer_id] = (
            time.ticks_add(time.ticks_ms(), interval),
            interval,
            tcb.callback,
            user_param,
        )
        return timer_id

    def SDL_RemoveTimer(timer):
        return 1 if _sw_timers.pop(timer, None) is not None else 0

else:
    _TIMER_MAX = const(8)
    _timer_slots = [None] * _TIMER_MAX  # (callback, user_param, ret_interval) or None
    _timer_id_to_slot = {}

    def _sw_timers_poll():
        pass  # ctypes timers run for real via SDL's own thread; nothing to poll.

    def _timer_trampoline(interval, slot):
        """
        Runs on an SDL-owned thread, but ctypes callbacks always re-acquire the
        GIL for us (PyGILState_Ensure()/Release() around every callback
        invocation), so this is safe unlike the MicroPython ffi case above.
        Looks the entry up through the slot table (not a raw pointer) so a
        concurrent SDL_RemoveTimer() cannot use freed state; mirrors
        timer_trampoline() in usdl2_cpy.c. The next interval is always the one
        the timer was created with (not the callback's return value).
        """
        entry = _timer_slots[slot] if 0 <= slot < _TIMER_MAX else None
        if entry is None:
            return 0
        callback, user_param, ret_interval = entry
        try:
            callback(interval, user_param)
        except Exception:
            pass
        return ret_interval

    _sdl_timer_functype = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t)
    _sdl_timer_cfunc = _sdl_timer_functype(_timer_trampoline)
    _lib_SDL_AddTimer = _libSDL2.SDL_AddTimer
    _lib_SDL_AddTimer.restype = ctypes.c_int
    _lib_SDL_AddTimer.argtypes = (ctypes.c_uint32, _sdl_timer_functype, ctypes.c_size_t)
    _lib_SDL_RemoveTimer = _libSDL2.SDL_RemoveTimer
    _lib_SDL_RemoveTimer.restype = ctypes.c_int
    _lib_SDL_RemoveTimer.argtypes = (ctypes.c_int,)

    def SDL_AddTimer(interval, tcb, user_param):
        if not isinstance(tcb, _TimerCallback):
            raise TypeError("callback must be from SDL_TimerCallback()")
        slot = -1
        for i in range(_TIMER_MAX):
            if _timer_slots[i] is None:
                slot = i
                break
        if slot < 0:
            raise RuntimeError("too many SDL timers")
        _timer_slots[slot] = (tcb.callback, user_param, interval)
        timer_id = _lib_SDL_AddTimer(interval, _sdl_timer_cfunc, slot)
        if not timer_id:
            _timer_slots[slot] = None
            return 0
        _timer_id_to_slot[timer_id] = slot
        return timer_id

    def SDL_RemoveTimer(timer):
        slot = _timer_id_to_slot.pop(timer, None)
        if slot is not None:
            _timer_slots[slot] = None
        return 1 if _lib_SDL_RemoveTimer(timer) else 0


###############################################################################
#                          Buffer-taking wrappers                             #
###############################################################################

# Defined once, backend-independent: _wrap_buf() and the private _lib_SDL_*
# names above are already backend-specific; the logic here mirrors
# usdl2_cpy.c's Python-facing signatures exactly. SDL_PumpEvents()/
# SDL_PollEvent() also drive the MicroPython software-timer poll above (a
# no-op on the ctypes backend, where real SDL timers do the work).


def SDL_PumpEvents():
    _lib_SDL_PumpEvents()
    _sw_timers_poll()


def SDL_PollEvent(event):
    _sw_timers_poll()
    data = event._data if isinstance(event, SDL_Event) else event
    return bool(_lib_SDL_PollEvent(_wrap_buf(data, writable=True)))


def SDL_UpdateTexture(texture, rect, pixels, pitch):
    return _lib_SDL_UpdateTexture(texture, _wrap_buf(rect), _wrap_buf(pixels), pitch)


def SDL_RenderReadPixels(renderer, rect, format, pixels, pitch):
    rc = _lib_SDL_RenderReadPixels(
        renderer, _wrap_buf(rect), format, _wrap_buf(pixels, writable=True), pitch
    )
    if rc != 0:
        raise RuntimeError(SDL_GetError())


def SDL_GetDisplayUsableBounds(display_index, rect=None):
    return _lib_SDL_GetDisplayUsableBounds(
        display_index, _wrap_buf(rect, writable=True)
    )


def SDL_GetDesktopDisplayMode(display_index, mode=None):
    return _lib_SDL_GetDesktopDisplayMode(
        display_index, _wrap_buf(mode, writable=True)
    )
