# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Pure-Python Win32 subset for CPython and MicroPython on Windows.

Used by ``displaydev.windisplay``, ``multimer``'s win32 timer backend, and
``audiodev.win_audio``. Supports ``ffi`` on MicroPython Windows and ``ctypes``
on CPython Windows.

Exports real Win32 / WASAPI names (plus a few thin COM helpers that wrap
vtable calls). Policy (eventsys mapping, PCM coalesce, timer ``_deliver``)
stays in the consumers.
"""

import struct
import sys

if sys.platform != "win32":
    raise ImportError("uwin32 requires Windows")

_use_ffi = False
if getattr(sys.implementation, "name", "") == "micropython":
    try:
        import ffi  # noqa: F401

        _use_ffi = True
    except ImportError:
        pass

if not _use_ffi and getattr(sys.implementation, "name", "") != "cpython":
    raise ImportError("uwin32 requires MicroPython ffi or CPython ctypes")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
CW_USEDEFAULT = -2147483648
IDC_ARROW = 32512
COLOR_WINDOW = 5
SW_SHOW = 5
SW_HIDE = 0
PM_REMOVE = 0x0001
ERROR_CLASS_ALREADY_EXISTS = 1410

WS_OVERLAPPED = 0x00000000
WS_CAPTION = 0x00C00000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_VISIBLE = 0x10000000
WS_CLIPCHILDREN = 0x02000000
WS_CLIPSIBLINGS = 0x04000000
WS_DISPLAY = (
    WS_OVERLAPPED
    | WS_CAPTION
    | WS_SYSMENU
    | WS_MINIMIZEBOX
    | WS_VISIBLE
    | WS_CLIPCHILDREN
    | WS_CLIPSIBLINGS
)

WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_QUIT = 0x0012
WM_PAINT = 0x000F
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MOUSEWHEEL = 0x020A
WM_MOUSEHWHEEL = 0x020E

MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_MBUTTON = 0x0010
WHEEL_DELTA = 120

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_END = 0x23
VK_HOME = 0x24
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_INSERT = 0x2D
VK_DELETE = 0x2E
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_F1 = 0x70

BI_RGB = 0
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020
SPI_GETWORKAREA = 0x0030

INFINITE = 0xFFFFFFFF
CREATE_WAITABLE_TIMER_HIGH_RESOLUTION = 0x00000002
TIMER_ALL_ACCESS = 0x1F0003
WT_EXECUTEDEFAULT = 0x00000000

COINIT_MULTITHREADED = 0x0
COINIT_APARTMENTTHREADED = 0x2
CLSCTX_ALL = 0x17
S_OK = 0
S_FALSE = 1
RPC_E_CHANGED_MODE = 0x80010106

eRender = 0
eCapture = 1
eConsole = 0
AUDCLNT_SHAREMODE_SHARED = 0
AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM = 0x80000000
AUDCLNT_STREAMFLAGS_SRC_DEFAULT_QUALITY = 0x08000000
WAVE_FORMAT_PCM = 1

# SDL-style keycodes used by keys.py
_SDLK_SCANCODE_MASK = 1 << 30
KMOD_LSHIFT = 0x0001
KMOD_RSHIFT = 0x0002
KMOD_LCTRL = 0x0040
KMOD_RCTRL = 0x0080
KMOD_LALT = 0x0100
KMOD_RALT = 0x0200
KMOD_LGUI = 0x0400
KMOD_RGUI = 0x0800

SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010

_IS_64 = sys.maxsize > 2**32
_PTR_SIZE = 8 if _IS_64 else 4

# ---------------------------------------------------------------------------
# Backend Implementation
# ---------------------------------------------------------------------------

if _use_ffi:
    import uctypes

    user32 = ffi.open("user32.dll")
    gdi32 = ffi.open("gdi32.dll")
    kernel32 = ffi.open("kernel32.dll")
    ole32 = ffi.open("ole32.dll")

    _L = "q" if _IS_64 else "i"
    _W = "Q" if _IS_64 else "I"

    _raw_DefWindowProcW = user32.func(_L, "DefWindowProcW", "PI" + _W + _L)
    _raw_RegisterClassExW = user32.func("H", "RegisterClassExW", "p")
    _raw_CreateWindowExW = user32.func("P", "CreateWindowExW", "IPPIiiiiPPPP")
    _raw_DestroyWindow = user32.func("i", "DestroyWindow", "P")
    _raw_ShowWindow = user32.func("i", "ShowWindow", "Pi")
    _raw_UpdateWindow = user32.func("i", "UpdateWindow", "P")
    _raw_GetClientRect = user32.func("i", "GetClientRect", "Pp")
    _raw_GetWindowRect = user32.func("i", "GetWindowRect", "Pp")
    _raw_AdjustWindowRectEx = user32.func("i", "AdjustWindowRectEx", "pIiI")
    _raw_SetWindowPos = user32.func("i", "SetWindowPos", "PPiiiiI")
    _raw_GetDC = user32.func("P", "GetDC", "P")
    _raw_ReleaseDC = user32.func("i", "ReleaseDC", "PP")
    _raw_BeginPaint = user32.func("P", "BeginPaint", "Pp")
    _raw_EndPaint = user32.func("i", "EndPaint", "Pp")
    _raw_InvalidateRect = user32.func("i", "InvalidateRect", "Ppi")
    _raw_ValidateRect = user32.func("i", "ValidateRect", "Pp")
    _raw_PeekMessageW = user32.func("i", "PeekMessageW", "pPIII")
    _raw_TranslateMessage = user32.func("i", "TranslateMessage", "p")
    _raw_DispatchMessageW = user32.func(_L, "DispatchMessageW", "p")
    _raw_PostQuitMessage = user32.func("v", "PostQuitMessage", "i")
    _raw_PostMessageW = user32.func("i", "PostMessageW", "PI" + _W + _L)
    _raw_GetMessageW = user32.func("i", "GetMessageW", "pPII")
    _raw_LoadCursorW = user32.func("P", "LoadCursorW", "PP")
    _raw_GetSystemMetrics = user32.func("i", "GetSystemMetrics", "i")
    _raw_SystemParametersInfoW = user32.func("i", "SystemParametersInfoW", "IIpI")
    _raw_ScreenToClient = user32.func("i", "ScreenToClient", "Pp")
    _raw_GetAsyncKeyState = user32.func("h", "GetAsyncKeyState", "i")
    _raw_MapVirtualKeyW = user32.func("I", "MapVirtualKeyW", "II")
    _raw_GetKeyNameTextW = user32.func("i", "GetKeyNameTextW", "qpi" if _IS_64 else "ipi")
    _raw_SetWindowTextW = user32.func("i", "SetWindowTextW", "PP")
    _raw_GetWindowLongPtrW = user32.func(_L, "GetWindowLongPtrW", "Pi")
    _raw_SetWindowLongPtrW = user32.func(_L, "SetWindowLongPtrW", "Pi" + _L)

    _raw_StretchDIBits = gdi32.func("i", "StretchDIBits", "PiiiiiiiiPpiI")
    _raw_SetDIBitsToDevice = gdi32.func("i", "SetDIBitsToDevice", "PiiIIiiiiPpi")

    _raw_GetModuleHandleW = kernel32.func("P", "GetModuleHandleW", "P")
    _raw_GetLastError = kernel32.func("I", "GetLastError", "")
    _raw_CloseHandle = kernel32.func("i", "CloseHandle", "P")
    _raw_SleepEx = kernel32.func("I", "SleepEx", "Ii")
    _raw_WaitForSingleObjectEx = kernel32.func("I", "WaitForSingleObjectEx", "PIi")
    _raw_CreateWaitableTimerExW = kernel32.func("P", "CreateWaitableTimerExW", "PPII")
    _raw_CreateWaitableTimerW = kernel32.func("P", "CreateWaitableTimerW", "PiP")
    _raw_SetWaitableTimer = kernel32.func("i", "SetWaitableTimer", "PpiPPi")
    _raw_CancelWaitableTimer = kernel32.func("i", "CancelWaitableTimer", "P")

    _raw_CoInitializeEx = ole32.func("i", "CoInitializeEx", "PI")
    _raw_CoUninitialize = ole32.func("v", "CoUninitialize", "")
    _raw_CoCreateInstance = ole32.func("i", "CoCreateInstance", "pPIpp")
    _raw_CoTaskMemFree = ole32.func("v", "CoTaskMemFree", "P")

    def _wstr(s):
        if s is None:
            return None
        if isinstance(s, (bytes, bytearray)):
            return s
        return bytes(b for c in s for b in (ord(c) & 0xFF, (ord(c) >> 8) & 0xFF)) + b"\x00\x00"

    def _wstr_decode(buf, nchars):
        return "".join(
            chr(buf[i * 2] | (buf[i * 2 + 1] << 8))
            for i in range(nchars)
            if (buf[i * 2] | (buf[i * 2 + 1] << 8)) != 0
        )


    def byref(obj):
        if hasattr(obj, "_buf"):
            return obj._buf
        return obj

    def sizeof(obj):
        if isinstance(obj, type) and hasattr(obj, "_SIZE"):
            return obj._SIZE
        if hasattr(obj, "_buf"):
            return len(obj._buf)
        if isinstance(obj, (bytes, bytearray)):
            return len(obj)
        return _PTR_SIZE

    _raw_RtlMoveMemory = kernel32.func("v", "RtlMoveMemory", "Ppi")

    def memmove(dst, src, count):
        if isinstance(dst, int):
            dst_addr = dst
        else:
            dst_addr = uctypes.addressof(dst)
        _raw_RtlMoveMemory(dst_addr, src, int(count))

    def string_at(ptr, size):
        return uctypes.bytes_at(ptr, int(size))

    def WNDPROC(fn):
        if callable(fn):
            return ffi.callback(_L, fn, "PI" + _W + _L)
        return fn

    def TIMERAPCROUTINE(fn=None):
        if callable(fn):
            return ffi.callback("v", fn, "PII")
        return None

    class POINT:
        _SIZE = 8

        def __init__(self, x=0, y=0, buf=None, offset=0):
            if buf is None:
                self._buf = bytearray(8)
                self._offset = 0
            else:
                self._buf = buf
                self._offset = offset
            if x or y:
                self.x = x
                self.y = y

        @property
        def x(self):
            return struct.unpack_from("<i", self._buf, self._offset)[0]

        @x.setter
        def x(self, val):
            struct.pack_into("<i", self._buf, self._offset, int(val))

        @property
        def y(self):
            return struct.unpack_from("<i", self._buf, self._offset + 4)[0]

        @y.setter
        def y(self, val):
            struct.pack_into("<i", self._buf, self._offset + 4, int(val))

    class RECT:
        _SIZE = 16

        def __init__(self, left=0, top=0, right=0, bottom=0, buf=None, offset=0):
            if buf is None:
                self._buf = bytearray(16)
                self._offset = 0
            else:
                self._buf = buf
                self._offset = offset
            if left or top or right or bottom:
                self.left = left
                self.top = top
                self.right = right
                self.bottom = bottom

        @property
        def left(self):
            return struct.unpack_from("<i", self._buf, self._offset)[0]

        @left.setter
        def left(self, val):
            struct.pack_into("<i", self._buf, self._offset, int(val))

        @property
        def top(self):
            return struct.unpack_from("<i", self._buf, self._offset + 4)[0]

        @top.setter
        def top(self, val):
            struct.pack_into("<i", self._buf, self._offset + 4, int(val))

        @property
        def right(self):
            return struct.unpack_from("<i", self._buf, self._offset + 8)[0]

        @right.setter
        def right(self, val):
            struct.pack_into("<i", self._buf, self._offset + 8, int(val))

        @property
        def bottom(self):
            return struct.unpack_from("<i", self._buf, self._offset + 12)[0]

        @bottom.setter
        def bottom(self, val):
            struct.pack_into("<i", self._buf, self._offset + 12, int(val))

    class MSG:
        _SIZE = 48 if _IS_64 else 28

        def __init__(self):
            self._buf = bytearray(self._SIZE)
            self.pt = POINT(buf=self._buf, offset=24 if _IS_64 else 16)

        @property
        def hwnd(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 0)[0]

        @hwnd.setter
        def hwnd(self, val):
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 0, int(val or 0))

        @property
        def message(self):
            return struct.unpack_from("<I", self._buf, 8 if _IS_64 else 4)[0]

        @message.setter
        def message(self, val):
            struct.pack_into("<I", self._buf, 8 if _IS_64 else 4, int(val))

        @property
        def wParam(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 16 if _IS_64 else 8)[0]

        @wParam.setter
        def wParam(self, val):
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 16 if _IS_64 else 8, int(val))

        @property
        def lParam(self):
            return struct.unpack_from("<" + ("q" if _IS_64 else "i"), self._buf, 24 if _IS_64 else 12)[0]

        @lParam.setter
        def lParam(self, val):
            struct.pack_into("<" + ("q" if _IS_64 else "i"), self._buf, 24 if _IS_64 else 12, int(val))

        @property
        def time(self):
            return struct.unpack_from("<I", self._buf, 32 if _IS_64 else 16)[0]

        @time.setter
        def time(self, val):
            struct.pack_into("<I", self._buf, 32 if _IS_64 else 16, int(val))

    class WNDCLASSEXW:
        _SIZE = 80 if _IS_64 else 48

        def __init__(self):
            self._buf = bytearray(self._SIZE)
            self._keepalive = []
            self.cbSize = self._SIZE

        @property
        def cbSize(self):
            return struct.unpack_from("<I", self._buf, 0)[0]

        @cbSize.setter
        def cbSize(self, val):
            struct.pack_into("<I", self._buf, 0, int(val))

        @property
        def style(self):
            return struct.unpack_from("<I", self._buf, 4)[0]

        @style.setter
        def style(self, val):
            struct.pack_into("<I", self._buf, 4, int(val))

        @property
        def lpfnWndProc(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 8)[0]

        @lpfnWndProc.setter
        def lpfnWndProc(self, val):
            self._keepalive.append(val)
            addr = val.cfun() if hasattr(val, "cfun") else int(val or 0)
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 8, addr)

        @property
        def cbClsExtra(self):
            return struct.unpack_from("<i", self._buf, 16 if _IS_64 else 12)[0]

        @cbClsExtra.setter
        def cbClsExtra(self, val):
            struct.pack_into("<i", self._buf, 16 if _IS_64 else 12, int(val))

        @property
        def cbWndExtra(self):
            return struct.unpack_from("<i", self._buf, 20 if _IS_64 else 16)[0]

        @cbWndExtra.setter
        def cbWndExtra(self, val):
            struct.pack_into("<i", self._buf, 20 if _IS_64 else 16, int(val))

        @property
        def hInstance(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 24 if _IS_64 else 20)[0]

        @hInstance.setter
        def hInstance(self, val):
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 24 if _IS_64 else 20, int(val or 0))

        @property
        def hIcon(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 32 if _IS_64 else 24)[0]

        @hIcon.setter
        def hIcon(self, val):
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 32 if _IS_64 else 24, int(val or 0))

        @property
        def hCursor(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 40 if _IS_64 else 28)[0]

        @hCursor.setter
        def hCursor(self, val):
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 40 if _IS_64 else 28, int(val or 0))

        @property
        def hbrBackground(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 48 if _IS_64 else 32)[0]

        @hbrBackground.setter
        def hbrBackground(self, val):
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 48 if _IS_64 else 32, int(val or 0))

        @property
        def lpszMenuName(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 56 if _IS_64 else 36)[0]

        @lpszMenuName.setter
        def lpszMenuName(self, val):
            if val is None:
                addr = 0
            elif isinstance(val, int):
                addr = val
            else:
                w = _wstr(val)
                self._keepalive.append(w)
                addr = uctypes.addressof(w)
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 56 if _IS_64 else 36, addr)

        @property
        def lpszClassName(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 64 if _IS_64 else 40)[0]

        @lpszClassName.setter
        def lpszClassName(self, val):
            if val is None:
                addr = 0
            elif isinstance(val, int):
                addr = val
            else:
                w = _wstr(val)
                self._keepalive.append(w)
                addr = uctypes.addressof(w)
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 64 if _IS_64 else 40, addr)

        @property
        def hIconSm(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 72 if _IS_64 else 44)[0]

        @hIconSm.setter
        def hIconSm(self, val):
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 72 if _IS_64 else 44, int(val or 0))

    class PAINTSTRUCT:
        _SIZE = 72 if _IS_64 else 64

        def __init__(self):
            self._buf = bytearray(self._SIZE)
            self.rcPaint = RECT(buf=self._buf, offset=8 if _IS_64 else 4)

        @property
        def hdc(self):
            return struct.unpack_from("<" + ("Q" if _IS_64 else "I"), self._buf, 0)[0]

        @hdc.setter
        def hdc(self, val):
            struct.pack_into("<" + ("Q" if _IS_64 else "I"), self._buf, 0, int(val or 0))

        @property
        def fErase(self):
            return bool(struct.unpack_from("<i", self._buf, 4)[0])

        @fErase.setter
        def fErase(self, val):
            struct.pack_into("<i", self._buf, 4, int(bool(val)))

        @property
        def fRestore(self):
            return bool(struct.unpack_from("<i", self._buf, 24 if _IS_64 else 20)[0])

        @fRestore.setter
        def fRestore(self, val):
            struct.pack_into("<i", self._buf, 24 if _IS_64 else 20, int(bool(val)))

        @property
        def fIncUpdate(self):
            return bool(struct.unpack_from("<i", self._buf, 28 if _IS_64 else 24)[0])

        @fIncUpdate.setter
        def fIncUpdate(self, val):
            struct.pack_into("<i", self._buf, 28 if _IS_64 else 24, int(bool(val)))

    class BITMAPINFOHEADER:
        _SIZE = 40

        def __init__(self, buf=None, offset=0):
            if buf is None:
                self._buf = bytearray(40)
                self._offset = 0
            else:
                self._buf = buf
                self._offset = offset
            self.biSize = 40

        @property
        def biSize(self):
            return struct.unpack_from("<I", self._buf, self._offset)[0]

        @biSize.setter
        def biSize(self, val):
            struct.pack_into("<I", self._buf, self._offset, int(val))

        @property
        def biWidth(self):
            return struct.unpack_from("<i", self._buf, self._offset + 4)[0]

        @biWidth.setter
        def biWidth(self, val):
            struct.pack_into("<i", self._buf, self._offset + 4, int(val))

        @property
        def biHeight(self):
            return struct.unpack_from("<i", self._buf, self._offset + 8)[0]

        @biHeight.setter
        def biHeight(self, val):
            struct.pack_into("<i", self._buf, self._offset + 8, int(val))

        @property
        def biPlanes(self):
            return struct.unpack_from("<H", self._buf, self._offset + 12)[0]

        @biPlanes.setter
        def biPlanes(self, val):
            struct.pack_into("<H", self._buf, self._offset + 12, int(val))

        @property
        def biBitCount(self):
            return struct.unpack_from("<H", self._buf, self._offset + 14)[0]

        @biBitCount.setter
        def biBitCount(self, val):
            struct.pack_into("<H", self._buf, self._offset + 14, int(val))

        @property
        def biCompression(self):
            return struct.unpack_from("<I", self._buf, self._offset + 16)[0]

        @biCompression.setter
        def biCompression(self, val):
            struct.pack_into("<I", self._buf, self._offset + 16, int(val))

        @property
        def biSizeImage(self):
            return struct.unpack_from("<I", self._buf, self._offset + 20)[0]

        @biSizeImage.setter
        def biSizeImage(self, val):
            struct.pack_into("<I", self._buf, self._offset + 20, int(val))

        @property
        def biXPelsPerMeter(self):
            return struct.unpack_from("<i", self._buf, self._offset + 24)[0]

        @biXPelsPerMeter.setter
        def biXPelsPerMeter(self, val):
            struct.pack_into("<i", self._buf, self._offset + 24, int(val))

        @property
        def biYPelsPerMeter(self):
            return struct.unpack_from("<i", self._buf, self._offset + 28)[0]

        @biYPelsPerMeter.setter
        def biYPelsPerMeter(self, val):
            struct.pack_into("<i", self._buf, self._offset + 28, int(val))

        @property
        def biClrUsed(self):
            return struct.unpack_from("<I", self._buf, self._offset + 32)[0]

        @biClrUsed.setter
        def biClrUsed(self, val):
            struct.pack_into("<I", self._buf, self._offset + 32, int(val))

        @property
        def biClrImportant(self):
            return struct.unpack_from("<I", self._buf, self._offset + 36)[0]

        @biClrImportant.setter
        def biClrImportant(self, val):
            struct.pack_into("<I", self._buf, self._offset + 36, int(val))

    class BITMAPINFO:
        _SIZE = 52

        def __init__(self):
            self._buf = bytearray(52)
            self.bmiHeader = BITMAPINFOHEADER(buf=self._buf, offset=0)

    class GUID:
        _SIZE = 16

        def __init__(self, d1=0, d2=0, d3=0, d4=None):
            self._buf = bytearray(16)
            if d1 or d2 or d3 or d4:
                self.Data1 = d1
                self.Data2 = d2
                self.Data3 = d3
                if d4:
                    self.Data4 = d4

        @property
        def Data1(self):
            return struct.unpack_from("<I", self._buf, 0)[0]

        @Data1.setter
        def Data1(self, val):
            struct.pack_into("<I", self._buf, 0, int(val))

        @property
        def Data2(self):
            return struct.unpack_from("<H", self._buf, 4)[0]

        @Data2.setter
        def Data2(self, val):
            struct.pack_into("<H", self._buf, 4, int(val))

        @property
        def Data3(self):
            return struct.unpack_from("<H", self._buf, 6)[0]

        @Data3.setter
        def Data3(self, val):
            struct.pack_into("<H", self._buf, 6, int(val))

        @property
        def Data4(self):
            return list(self._buf[8:16])

        @Data4.setter
        def Data4(self, val):
            for i, b in enumerate(val[:8]):
                self._buf[8 + i] = int(b)

    class WAVEFORMATEX:
        _SIZE = 18

        def __init__(self):
            self._buf = bytearray(18)

        @property
        def wFormatTag(self):
            return struct.unpack_from("<H", self._buf, 0)[0]

        @wFormatTag.setter
        def wFormatTag(self, val):
            struct.pack_into("<H", self._buf, 0, int(val))

        @property
        def nChannels(self):
            return struct.unpack_from("<H", self._buf, 2)[0]

        @nChannels.setter
        def nChannels(self, val):
            struct.pack_into("<H", self._buf, 2, int(val))

        @property
        def nSamplesPerSec(self):
            return struct.unpack_from("<I", self._buf, 4)[0]

        @nSamplesPerSec.setter
        def nSamplesPerSec(self, val):
            struct.pack_into("<I", self._buf, 4, int(val))

        @property
        def nAvgBytesPerSec(self):
            return struct.unpack_from("<I", self._buf, 8)[0]

        @nAvgBytesPerSec.setter
        def nAvgBytesPerSec(self, val):
            struct.pack_into("<I", self._buf, 8, int(val))

        @property
        def nBlockAlign(self):
            return struct.unpack_from("<H", self._buf, 12)[0]

        @nBlockAlign.setter
        def nBlockAlign(self, val):
            struct.pack_into("<H", self._buf, 12, int(val))

        @property
        def wBitsPerSample(self):
            return struct.unpack_from("<H", self._buf, 14)[0]

        @wBitsPerSample.setter
        def wBitsPerSample(self, val):
            struct.pack_into("<H", self._buf, 14, int(val))

        @property
        def cbSize(self):
            return struct.unpack_from("<H", self._buf, 16)[0]

        @cbSize.setter
        def cbSize(self, val):
            struct.pack_into("<H", self._buf, 16, int(val))

    BOOL = int
    DWORD = int
    WORD = int
    LONG = int
    ULONG = int
    HWND = int
    HDC = int
    HINSTANCE = int
    HMENU = int
    HICON = int
    HCURSOR = int
    HBRUSH = int
    HBITMAP = int
    HANDLE = int
    LPARAM = int
    WPARAM = int
    UINT = int
    LPCWSTR = str
    LPWSTR = str
    ATOM = int
    BYTE = int
    WCHAR = str
    HRESULT = int
    INT = int
    UINT32 = int
    INT64 = int
    UINT64 = int
    LRESULT = int
    LPVOID = int
    LPCVOID = int

    def _ptr_read(addr):
        return struct.unpack("<" + ("Q" if _IS_64 else "I"), uctypes.bytearray_at(addr, _PTR_SIZE))[0]

    def _vcall(punk, index, rettype_code, argtypes_str, *args):
        if not punk:
            raise OSError("NULL COM pointer")
        vtbl = _ptr_read(punk)
        fn_addr = _ptr_read(vtbl + index * _PTR_SIZE)
        if isinstance(argtypes_str, (tuple, list)):
            argtypes_str = "".join(argtypes_str)
        fn = ffi.func(rettype_code, fn_addr, "P" + argtypes_str)
        return fn(punk, *args)

else:
    import ctypes
    from ctypes import POINTER, byref, c_void_p, sizeof, windll, wintypes

    try:
        user32 = windll.user32
        gdi32 = windll.gdi32
        kernel32 = windll.kernel32
        ole32 = windll.ole32
    except Exception as exc:
        raise ImportError("uwin32 could not load Win32 DLLs") from exc

    BOOL = wintypes.BOOL
    DWORD = wintypes.DWORD
    WORD = wintypes.WORD
    LONG = wintypes.LONG
    ULONG = wintypes.ULONG
    HWND = wintypes.HWND
    HDC = wintypes.HDC
    HINSTANCE = wintypes.HINSTANCE
    HMENU = wintypes.HMENU
    HICON = wintypes.HICON
    HCURSOR = wintypes.HCURSOR
    HBRUSH = wintypes.HBRUSH
    HBITMAP = wintypes.HBITMAP
    HANDLE = wintypes.HANDLE
    LPARAM = wintypes.LPARAM
    WPARAM = wintypes.WPARAM
    UINT = wintypes.UINT
    LPCWSTR = wintypes.LPCWSTR
    LPWSTR = wintypes.LPWSTR
    ATOM = wintypes.ATOM
    BYTE = wintypes.BYTE
    WCHAR = wintypes.WCHAR
    HRESULT = ctypes.c_long
    INT = ctypes.c_int
    UINT32 = ctypes.c_uint32
    INT64 = ctypes.c_int64
    UINT64 = ctypes.c_uint64
    LRESULT = ctypes.c_ssize_t
    LPVOID = c_void_p
    LPCVOID = c_void_p

    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)
    TIMERAPCROUTINE = ctypes.WINFUNCTYPE(None, c_void_p, DWORD, DWORD)

    class POINT(ctypes.Structure):
        _fields_ = [("x", LONG), ("y", LONG)]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", LONG),
            ("top", LONG),
            ("right", LONG),
            ("bottom", LONG),
        ]

    class MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd", HWND),
            ("message", UINT),
            ("wParam", WPARAM),
            ("lParam", LPARAM),
            ("time", DWORD),
            ("pt", POINT),
        ]

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", UINT),
            ("style", UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", INT),
            ("cbWndExtra", INT),
            ("hInstance", HINSTANCE),
            ("hIcon", HICON),
            ("hCursor", HCURSOR),
            ("hbrBackground", HBRUSH),
            ("lpszMenuName", LPCWSTR),
            ("lpszClassName", LPCWSTR),
            ("hIconSm", HICON),
        ]

    class PAINTSTRUCT(ctypes.Structure):
        _fields_ = [
            ("hdc", HDC),
            ("fErase", BOOL),
            ("rcPaint", RECT),
            ("fRestore", BOOL),
            ("fIncUpdate", BOOL),
            ("rgbReserved", BYTE * 32),
        ]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", DWORD),
            ("biWidth", LONG),
            ("biHeight", LONG),
            ("biPlanes", WORD),
            ("biBitCount", WORD),
            ("biCompression", DWORD),
            ("biSizeImage", DWORD),
            ("biXPelsPerMeter", LONG),
            ("biYPelsPerMeter", LONG),
            ("biClrUsed", DWORD),
            ("biClrImportant", DWORD),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", DWORD * 3),
        ]

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", DWORD),
            ("Data2", WORD),
            ("Data3", WORD),
            ("Data4", BYTE * 8),
        ]

    class WAVEFORMATEX(ctypes.Structure):
        _pack_ = 1
        _fields_ = [
            ("wFormatTag", WORD),
            ("nChannels", WORD),
            ("nSamplesPerSec", DWORD),
            ("nAvgBytesPerSec", DWORD),
            ("nBlockAlign", WORD),
            ("wBitsPerSample", WORD),
            ("cbSize", WORD),
        ]

    user32.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    user32.DefWindowProcW.restype = LRESULT
    user32.RegisterClassExW.argtypes = [POINTER(WNDCLASSEXW)]
    user32.RegisterClassExW.restype = ATOM
    user32.CreateWindowExW.argtypes = [
        DWORD,
        LPCWSTR,
        LPCWSTR,
        DWORD,
        INT,
        INT,
        INT,
        INT,
        HWND,
        HMENU,
        HINSTANCE,
        LPVOID,
    ]
    user32.CreateWindowExW.restype = HWND
    user32.DestroyWindow.argtypes = [HWND]
    user32.DestroyWindow.restype = BOOL
    user32.ShowWindow.argtypes = [HWND, INT]
    user32.ShowWindow.restype = BOOL
    user32.UpdateWindow.argtypes = [HWND]
    user32.UpdateWindow.restype = BOOL
    user32.GetClientRect.argtypes = [HWND, POINTER(RECT)]
    user32.GetClientRect.restype = BOOL
    user32.GetWindowRect.argtypes = [HWND, POINTER(RECT)]
    user32.GetWindowRect.restype = BOOL
    user32.AdjustWindowRectEx.argtypes = [POINTER(RECT), DWORD, BOOL, DWORD]
    user32.AdjustWindowRectEx.restype = BOOL
    user32.SetWindowPos.argtypes = [HWND, HWND, INT, INT, INT, INT, UINT]
    user32.SetWindowPos.restype = BOOL
    user32.GetDC.argtypes = [HWND]
    user32.GetDC.restype = HDC
    user32.ReleaseDC.argtypes = [HWND, HDC]
    user32.ReleaseDC.restype = INT
    user32.BeginPaint.argtypes = [HWND, POINTER(PAINTSTRUCT)]
    user32.BeginPaint.restype = HDC
    user32.EndPaint.argtypes = [HWND, POINTER(PAINTSTRUCT)]
    user32.EndPaint.restype = BOOL
    user32.InvalidateRect.argtypes = [HWND, POINTER(RECT), BOOL]
    user32.InvalidateRect.restype = BOOL
    user32.ValidateRect.argtypes = [HWND, POINTER(RECT)]
    user32.ValidateRect.restype = BOOL
    user32.PeekMessageW.argtypes = [POINTER(MSG), HWND, UINT, UINT, UINT]
    user32.PeekMessageW.restype = BOOL
    user32.TranslateMessage.argtypes = [POINTER(MSG)]
    user32.TranslateMessage.restype = BOOL
    user32.DispatchMessageW.argtypes = [POINTER(MSG)]
    user32.DispatchMessageW.restype = LRESULT
    user32.PostQuitMessage.argtypes = [INT]
    user32.PostQuitMessage.restype = None
    user32.PostMessageW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    user32.PostMessageW.restype = BOOL
    user32.GetMessageW.argtypes = [POINTER(MSG), HWND, UINT, UINT]
    user32.GetMessageW.restype = BOOL
    user32.LoadCursorW.argtypes = [HINSTANCE, LPCWSTR]
    user32.LoadCursorW.restype = HCURSOR
    user32.GetSystemMetrics.argtypes = [INT]
    user32.GetSystemMetrics.restype = INT
    user32.SystemParametersInfoW.argtypes = [UINT, UINT, LPVOID, UINT]
    user32.SystemParametersInfoW.restype = BOOL
    user32.ScreenToClient.argtypes = [HWND, POINTER(POINT)]
    user32.ScreenToClient.restype = BOOL
    user32.GetAsyncKeyState.argtypes = [INT]
    user32.GetAsyncKeyState.restype = wintypes.SHORT
    user32.MapVirtualKeyW.argtypes = [UINT, UINT]
    user32.MapVirtualKeyW.restype = UINT
    user32.GetKeyNameTextW.argtypes = [LONG, LPWSTR, INT]
    user32.GetKeyNameTextW.restype = INT
    user32.SetWindowTextW.argtypes = [HWND, LPCWSTR]
    user32.SetWindowTextW.restype = BOOL
    user32.GetWindowLongPtrW.argtypes = [HWND, INT]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [HWND, INT, ctypes.c_ssize_t]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t

    gdi32.StretchDIBits.argtypes = [
        HDC,
        INT,
        INT,
        INT,
        INT,
        INT,
        INT,
        INT,
        INT,
        LPCVOID,
        POINTER(BITMAPINFO),
        UINT,
        DWORD,
    ]
    gdi32.StretchDIBits.restype = INT
    gdi32.SetDIBitsToDevice.argtypes = [
        HDC,
        INT,
        INT,
        DWORD,
        DWORD,
        INT,
        INT,
        UINT,
        UINT,
        LPCVOID,
        POINTER(BITMAPINFO),
        UINT,
    ]
    gdi32.SetDIBitsToDevice.restype = INT

    kernel32.GetModuleHandleW.argtypes = [LPCWSTR]
    kernel32.GetModuleHandleW.restype = HINSTANCE
    kernel32.GetLastError.argtypes = []
    kernel32.GetLastError.restype = DWORD
    kernel32.CloseHandle.argtypes = [HANDLE]
    kernel32.CloseHandle.restype = BOOL
    kernel32.SleepEx.argtypes = [DWORD, BOOL]
    kernel32.SleepEx.restype = DWORD
    kernel32.WaitForSingleObjectEx.argtypes = [HANDLE, DWORD, BOOL]
    kernel32.WaitForSingleObjectEx.restype = DWORD
    kernel32.CreateWaitableTimerExW.argtypes = [LPVOID, LPCWSTR, DWORD, DWORD]
    kernel32.CreateWaitableTimerExW.restype = HANDLE
    kernel32.CreateWaitableTimerW.argtypes = [LPVOID, BOOL, LPCWSTR]
    kernel32.CreateWaitableTimerW.restype = HANDLE
    kernel32.SetWaitableTimer.argtypes = [
        HANDLE,
        POINTER(INT64),
        LONG,
        TIMERAPCROUTINE,
        LPVOID,
        BOOL,
    ]
    kernel32.SetWaitableTimer.restype = BOOL
    kernel32.CancelWaitableTimer.argtypes = [HANDLE]
    kernel32.CancelWaitableTimer.restype = BOOL

    ole32.CoInitializeEx.argtypes = [LPVOID, DWORD]
    ole32.CoInitializeEx.restype = HRESULT
    ole32.CoUninitialize.argtypes = []
    ole32.CoUninitialize.restype = None
    ole32.CoCreateInstance.argtypes = [
        POINTER(GUID),
        LPVOID,
        DWORD,
        POINTER(GUID),
        POINTER(c_void_p),
    ]
    ole32.CoCreateInstance.restype = HRESULT
    ole32.CoTaskMemFree.argtypes = [LPVOID]
    ole32.CoTaskMemFree.restype = None

    def _vtbl(punk):
        p = ctypes.cast(c_void_p(punk), POINTER(c_void_p))
        return ctypes.cast(p[0], POINTER(c_void_p))

    def _vcall(punk, index, restype, argtypes, *args):
        proto = ctypes.WINFUNCTYPE(restype, c_void_p, *argtypes)
        fn = proto(_vtbl(punk)[index])
        return fn(punk, *args)

    memmove = ctypes.memmove
    string_at = ctypes.string_at



# ---------------------------------------------------------------------------
# GUID Helpers
# ---------------------------------------------------------------------------

def _guid(d1, d2, d3, d4):
    g = GUID()
    g.Data1 = d1
    g.Data2 = d2
    g.Data3 = d3
    g.Data4 = d4
    return g


CLSID_MMDeviceEnumerator = _guid(
    0xBCDE0395, 0xE52F, 0x467C, (0x8E, 0x3D, 0xC4, 0x57, 0x92, 0x91, 0x69, 0x2E)
)
IID_IMMDeviceEnumerator = _guid(
    0xA95664D2, 0x9614, 0x4F35, (0xA7, 0x46, 0xDE, 0x8D, 0xB6, 0x36, 0x17, 0xE6)
)
IID_IAudioClient = _guid(
    0x1CB9AD4C, 0xDBFA, 0x4C32, (0xB1, 0x78, 0xC2, 0xF5, 0x68, 0xA7, 0x03, 0xB2)
)
IID_IAudioRenderClient = _guid(
    0xF294ACFC, 0x3146, 0x4483, (0xA7, 0xBF, 0xAD, 0xDC, 0xA7, 0xC2, 0x60, 0xE2)
)
IID_IAudioCaptureClient = _guid(
    0xC8ADBD64, 0xE71E, 0x48A0, (0xA4, 0xDE, 0x18, 0x5C, 0x39, 0x5C, 0xD3, 0x17)
)


# ---------------------------------------------------------------------------
# Thin helpers
# ---------------------------------------------------------------------------

def GET_X_LPARAM(lparam):
    lparam = int(lparam) & 0xFFFF
    return lparam - 65536 if lparam >= 32768 else lparam


def GET_Y_LPARAM(lparam):
    lparam = (int(lparam) >> 16) & 0xFFFF
    return lparam - 65536 if lparam >= 32768 else lparam


def GET_WHEEL_DELTA_WPARAM(wparam):
    wparam = (int(wparam) >> 16) & 0xFFFF
    return wparam - 65536 if wparam >= 32768 else wparam


def MAKEINTRESOURCE(value):
    if _use_ffi:
        return int(value)
    return ctypes.cast(value, LPCWSTR)


def hwnd_int(hwnd):
    if not hwnd:
        return 0
    return int(hwnd) if not isinstance(hwnd, int) else hwnd


def GetLastError():
    if _use_ffi:
        return int(_raw_GetLastError())
    return int(kernel32.GetLastError())


def DefWindowProcW(hwnd, msg, wparam, lparam):
    if _use_ffi:
        return int(_raw_DefWindowProcW(hwnd, int(msg), int(wparam), int(lparam)))
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def GetModuleHandleW(name=None):
    if _use_ffi:
        return _raw_GetModuleHandleW(_wstr(name) if name else None)
    return kernel32.GetModuleHandleW(name)


def LoadCursorW(instance, cursor):
    if _use_ffi:
        c = cursor if isinstance(cursor, int) else _wstr(cursor)
        return _raw_LoadCursorW(instance, c)
    if isinstance(cursor, int):
        cursor = MAKEINTRESOURCE(cursor)
    return user32.LoadCursorW(instance, cursor)


def RegisterClassExW(cls):
    if _use_ffi:
        atom = _raw_RegisterClassExW(cls._buf if hasattr(cls, "_buf") else cls)
        if not atom and GetLastError() != ERROR_CLASS_ALREADY_EXISTS:
            raise OSError("RegisterClassExW failed (%s)" % GetLastError())
        return atom
    atom = user32.RegisterClassExW(byref(cls))
    if not atom and GetLastError() != ERROR_CLASS_ALREADY_EXISTS:
        raise OSError("RegisterClassExW failed (%s)" % GetLastError())
    return atom


def CreateWindowExW(
    ex_style,
    class_name,
    window_name,
    style,
    x,
    y,
    width,
    height,
    parent=None,
    menu=None,
    instance=None,
    param=None,
):
    if _use_ffi:
        inst = instance if instance is not None else GetModuleHandleW()
        hwnd = _raw_CreateWindowExW(
            int(ex_style),
            _wstr(class_name),
            _wstr(window_name),
            int(style),
            int(x),
            int(y),
            int(width),
            int(height),
            parent,
            menu,
            inst,
            param,
        )
        if not hwnd:
            raise OSError("CreateWindowExW failed (%s)" % GetLastError())
        return hwnd
    hwnd = user32.CreateWindowExW(
        ex_style,
        class_name,
        window_name,
        style,
        x,
        y,
        width,
        height,
        parent,
        menu,
        instance or GetModuleHandleW(),
        param,
    )
    if not hwnd:
        raise OSError("CreateWindowExW failed (%s)" % GetLastError())
    return hwnd


def DestroyWindow(hwnd):
    if _use_ffi:
        return bool(_raw_DestroyWindow(hwnd))
    return bool(user32.DestroyWindow(hwnd))


def ShowWindow(hwnd, cmd=SW_SHOW):
    if _use_ffi:
        return bool(_raw_ShowWindow(hwnd, int(cmd)))
    return bool(user32.ShowWindow(hwnd, cmd))


def UpdateWindow(hwnd):
    if _use_ffi:
        return bool(_raw_UpdateWindow(hwnd))
    return bool(user32.UpdateWindow(hwnd))


def GetClientRect(hwnd):
    rect = RECT()
    if _use_ffi:
        if not _raw_GetClientRect(hwnd, rect._buf):
            return 0, 0, 0, 0
    else:
        if not user32.GetClientRect(hwnd, byref(rect)):
            return 0, 0, 0, 0
    return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)


def GetWindowRect(hwnd):
    rect = RECT()
    if _use_ffi:
        if not _raw_GetWindowRect(hwnd, rect._buf):
            return 0, 0, 0, 0
    else:
        if not user32.GetWindowRect(hwnd, byref(rect)):
            return 0, 0, 0, 0
    return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)


def AdjustWindowRectEx(width, height, style, ex_style=0):
    rect = RECT(0, 0, int(width), int(height))
    if _use_ffi:
        if not _raw_AdjustWindowRectEx(rect._buf, int(style), 0, int(ex_style)):
            return width, height
    else:
        if not user32.AdjustWindowRectEx(byref(rect), style, False, ex_style):
            return width, height
    return int(rect.right - rect.left), int(rect.bottom - rect.top)


def SetWindowPos(hwnd, x, y, width, height, flags=SWP_NOZORDER | SWP_NOACTIVATE):
    if _use_ffi:
        return bool(_raw_SetWindowPos(hwnd, None, int(x), int(y), int(width), int(height), int(flags)))
    return bool(user32.SetWindowPos(hwnd, None, x, y, width, height, flags))


def GetDC(hwnd):
    if _use_ffi:
        return _raw_GetDC(hwnd)
    return user32.GetDC(hwnd)


def ReleaseDC(hwnd, hdc):
    if _use_ffi:
        return int(_raw_ReleaseDC(hwnd, hdc))
    return user32.ReleaseDC(hwnd, hdc)


def BeginPaint(hwnd):
    ps = PAINTSTRUCT()
    if _use_ffi:
        hdc = _raw_BeginPaint(hwnd, ps._buf)
        return hdc, ps
    hdc = user32.BeginPaint(hwnd, byref(ps))
    return hdc, ps


def EndPaint(hwnd, ps):
    if _use_ffi:
        return bool(_raw_EndPaint(hwnd, ps._buf if hasattr(ps, "_buf") else ps))
    return bool(user32.EndPaint(hwnd, byref(ps)))


def InvalidateRect(hwnd, erase=False):
    if _use_ffi:
        return bool(_raw_InvalidateRect(hwnd, None, int(bool(erase))))
    return bool(user32.InvalidateRect(hwnd, None, bool(erase)))


def ValidateRect(hwnd):
    if _use_ffi:
        return bool(_raw_ValidateRect(hwnd, None))
    return bool(user32.ValidateRect(hwnd, None))


def PeekMessageW(hwnd=None, remove=True):
    msg = MSG()
    if _use_ffi:
        got = _raw_PeekMessageW(msg._buf, hwnd, 0, 0, PM_REMOVE if remove else 0)
        if not got:
            return None
        return msg
    got = user32.PeekMessageW(byref(msg), hwnd, 0, 0, PM_REMOVE if remove else 0)
    if not got:
        return None
    return msg


def TranslateMessage(msg):
    if _use_ffi:
        return bool(_raw_TranslateMessage(msg._buf if hasattr(msg, "_buf") else msg))
    return bool(user32.TranslateMessage(byref(msg)))


def DispatchMessageW(msg):
    if _use_ffi:
        return _raw_DispatchMessageW(msg._buf if hasattr(msg, "_buf") else msg)
    return user32.DispatchMessageW(byref(msg))


def PostQuitMessage(code=0):
    if _use_ffi:
        _raw_PostQuitMessage(int(code))
    else:
        user32.PostQuitMessage(int(code))


def PostMessageW(hwnd, msg, wparam=0, lparam=0):
    if _use_ffi:
        return bool(_raw_PostMessageW(hwnd, int(msg), int(wparam), int(lparam)))
    return bool(user32.PostMessageW(hwnd, msg, wparam, lparam))


def GetMessageW(hwnd=None, min_msg=0, max_msg=0):
    msg = MSG()
    if _use_ffi:
        res = _raw_GetMessageW(msg._buf, hwnd, int(min_msg), int(max_msg))
        return res, msg
    res = user32.GetMessageW(byref(msg), hwnd, min_msg, max_msg)
    return res, msg


def ScreenToClient(hwnd, x, y):
    pt = POINT(int(x), int(y))
    if _use_ffi:
        _raw_ScreenToClient(hwnd, pt._buf)
    else:
        user32.ScreenToClient(hwnd, byref(pt))
    return int(pt.x), int(pt.y)


def GetAsyncKeyState(vk):
    if _use_ffi:
        return int(_raw_GetAsyncKeyState(int(vk)))
    return int(user32.GetAsyncKeyState(int(vk)))


def MapVirtualKeyW(code, map_type=0):
    if _use_ffi:
        return int(_raw_MapVirtualKeyW(int(code), int(map_type)))
    return int(user32.MapVirtualKeyW(int(code), int(map_type)))


def SystemParametersInfoW_GETWORKAREA():
    rect = RECT()
    if _use_ffi:
        if not _raw_SystemParametersInfoW(SPI_GETWORKAREA, 0, rect._buf, 0):
            return 0, 0, 0, 0
    else:
        if not user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, byref(rect), 0):
            return 0, 0, 0, 0
    w = int(rect.right - rect.left)
    h = int(rect.bottom - rect.top)
    if w <= 0 or h <= 0:
        return 0, 0, 0, 0
    return int(rect.left), int(rect.top), w, h


def bmi_bgra(width, height):
    """32-bit top-down BI_RGB BITMAPINFO for BGRA pixels."""
    info = BITMAPINFO()
    info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
    info.bmiHeader.biWidth = int(width)
    info.bmiHeader.biHeight = -int(height)
    info.bmiHeader.biPlanes = 1
    info.bmiHeader.biBitCount = 32
    info.bmiHeader.biCompression = BI_RGB
    info.bmiHeader.biSizeImage = int(width) * int(height) * 4
    return info


def StretchDIBits(hdc, dest_w, dest_h, src_w, src_h, bits, bmi):
    if _use_ffi:
        bmi_buf = bmi._buf if hasattr(bmi, "_buf") else bmi
        return int(
            _raw_StretchDIBits(
                hdc,
                0,
                0,
                int(dest_w),
                int(dest_h),
                0,
                0,
                int(src_w),
                int(src_h),
                bits,
                bmi_buf,
                DIB_RGB_COLORS,
                SRCCOPY,
            )
        )
    return int(
        gdi32.StretchDIBits(
            hdc,
            0,
            0,
            int(dest_w),
            int(dest_h),
            0,
            0,
            int(src_w),
            int(src_h),
            bits,
            byref(bmi),
            DIB_RGB_COLORS,
            SRCCOPY,
        )
    )


def SetDIBitsToDevice(hdc, x_dst, y_dst, width, height, x_src, y_src, start_scan, scan_lines, bits, bmi):
    if _use_ffi:
        bmi_buf = bmi._buf if hasattr(bmi, "_buf") else bmi
        return int(
            _raw_SetDIBitsToDevice(
                hdc,
                int(x_dst),
                int(y_dst),
                int(width),
                int(height),
                int(x_src),
                int(y_src),
                int(start_scan),
                int(scan_lines),
                bits,
                bmi_buf,
                DIB_RGB_COLORS,
            )
        )
    return int(
        gdi32.SetDIBitsToDevice(
            hdc,
            int(x_dst),
            int(y_dst),
            int(width),
            int(height),
            int(x_src),
            int(y_src),
            int(start_scan),
            int(scan_lines),
            bits,
            byref(bmi),
            DIB_RGB_COLORS,
        )
    )


def GetKeyNameTextW(lparam):
    if _use_ffi:
        buf = bytearray(128)
        n = _raw_GetKeyNameTextW(int(lparam), buf, 64)
        if not n:
            return ""
        return _wstr_decode(buf, n)
    buf = ctypes.create_unicode_buffer(64)
    n = user32.GetKeyNameTextW(int(lparam), buf, 64)
    return buf.value if n else ""


def SetWindowTextW(hwnd, text):
    if _use_ffi:
        return bool(_raw_SetWindowTextW(hwnd, _wstr(text)))
    return bool(user32.SetWindowTextW(hwnd, text))


def GetWindowLongPtrW(hwnd, index):
    if _use_ffi:
        return _raw_GetWindowLongPtrW(hwnd, int(index))
    return user32.GetWindowLongPtrW(hwnd, int(index))


def SetWindowLongPtrW(hwnd, index, new_long):
    if _use_ffi:
        return _raw_SetWindowLongPtrW(hwnd, int(index), int(new_long))
    return user32.SetWindowLongPtrW(hwnd, int(index), int(new_long))


def modifier_mask():
    """SDL-style KMOD mask from GetAsyncKeyState."""
    mod = 0
    if GetAsyncKeyState(VK_LSHIFT) & 0x8000:
        mod |= KMOD_LSHIFT
    if GetAsyncKeyState(VK_RSHIFT) & 0x8000:
        mod |= KMOD_RSHIFT
    if GetAsyncKeyState(VK_LCONTROL) & 0x8000:
        mod |= KMOD_LCTRL
    if GetAsyncKeyState(VK_RCONTROL) & 0x8000:
        mod |= KMOD_RCTRL
    if GetAsyncKeyState(VK_LMENU) & 0x8000:
        mod |= KMOD_LALT
    if GetAsyncKeyState(VK_RMENU) & 0x8000:
        mod |= KMOD_RALT
    if GetAsyncKeyState(VK_LWIN) & 0x8000:
        mod |= KMOD_LGUI
    if GetAsyncKeyState(VK_RWIN) & 0x8000:
        mod |= KMOD_RGUI
    if not (mod & (KMOD_LSHIFT | KMOD_RSHIFT)) and GetAsyncKeyState(VK_SHIFT) & 0x8000:
        mod |= KMOD_LSHIFT
    if not (mod & (KMOD_LCTRL | KMOD_RCTRL)) and GetAsyncKeyState(VK_CONTROL) & 0x8000:
        mod |= KMOD_LCTRL
    if not (mod & (KMOD_LALT | KMOD_RALT)) and GetAsyncKeyState(VK_MENU) & 0x8000:
        mod |= KMOD_LALT
    return mod


_VK_SPECIAL = {
    VK_BACK: 8,
    VK_TAB: 9,
    VK_RETURN: 13,
    VK_ESCAPE: 27,
    VK_SPACE: 32,
    VK_DELETE: 127,
    VK_LEFT: 1073741904,
    VK_RIGHT: 1073741903,
    VK_UP: 1073741906,
    VK_DOWN: 1073741905,
    VK_HOME: 1073741898,
    VK_END: 1073741901,
    VK_PRIOR: 1073741899,
    VK_NEXT: 1073741902,
    VK_INSERT: 1073741897,
}


def virtual_key_to_sdl(vk):
    """Map a Win32 virtual-key code to an eventsys / SDL keycode."""
    vk = int(vk) & 0xFF
    if 0x41 <= vk <= 0x5A:
        return vk + 32  # 'A'..'Z' → 'a'..'z'
    if 0x30 <= vk <= 0x39:
        return vk  # '0'..'9'
    if VK_F1 <= vk <= VK_F1 + 11:
        return 1073741882 + (vk - VK_F1)
    if vk in _VK_SPECIAL:
        return _VK_SPECIAL[vk]
    return vk


# ---------------------------------------------------------------------------
# Timers
# ---------------------------------------------------------------------------

def CreateWaitableTimerExW(manual_reset=False, high_resolution=False):
    flags = 0
    if manual_reset:
        flags |= 0x00000001
    if high_resolution:
        flags |= CREATE_WAITABLE_TIMER_HIGH_RESOLUTION
    if _use_ffi:
        handle = _raw_CreateWaitableTimerExW(None, None, flags, TIMER_ALL_ACCESS)
        if handle:
            return handle
        handle = _raw_CreateWaitableTimerW(None, int(bool(manual_reset)), None)
        if not handle:
            raise OSError("CreateWaitableTimer failed (%s)" % GetLastError())
        return handle
    handle = kernel32.CreateWaitableTimerExW(None, None, flags, TIMER_ALL_ACCESS)
    if handle:
        return handle
    handle = kernel32.CreateWaitableTimerW(None, bool(manual_reset), None)
    if not handle:
        raise OSError("CreateWaitableTimer failed (%s)" % GetLastError())
    return handle


def SetWaitableTimer(handle, due_ms, period_ms, apc=None, arg=None):
    due_val = int(-max(1, int(due_ms)) * 10000)
    if _use_ffi:
        due_buf = struct.pack("<q", due_val)
        ok = _raw_SetWaitableTimer(
            handle,
            due_buf,
            int(period_ms),
            apc,
            arg,
            0,
        )
        if not ok:
            raise OSError("SetWaitableTimer failed (%s)" % GetLastError())
        return ok
    due = INT64(due_val)
    cb = apc if apc is not None else TIMERAPCROUTINE()
    ok = kernel32.SetWaitableTimer(
        handle,
        byref(due),
        int(period_ms),
        cb,
        arg,
        False,
    )
    if not ok:
        raise OSError("SetWaitableTimer failed (%s)" % GetLastError())
    return ok


def CancelWaitableTimer(handle):
    if _use_ffi:
        return bool(_raw_CancelWaitableTimer(handle))
    return bool(kernel32.CancelWaitableTimer(handle))


def CloseHandle(handle):
    if _use_ffi:
        return bool(_raw_CloseHandle(handle))
    return bool(kernel32.CloseHandle(handle))


def SleepEx(ms, alertable=True):
    if _use_ffi:
        return int(_raw_SleepEx(max(0, int(ms)), int(bool(alertable))))
    return int(kernel32.SleepEx(max(0, int(ms)), bool(alertable)))


def WaitForSingleObjectEx(handle, ms, alertable=True):
    if _use_ffi:
        return int(_raw_WaitForSingleObjectEx(handle, int(ms), int(bool(alertable))))
    return int(kernel32.WaitForSingleObjectEx(handle, int(ms), bool(alertable)))


# ---------------------------------------------------------------------------
# COM / WASAPI
# ---------------------------------------------------------------------------

def SUCCEEDED(hr):
    return int(hr) >= 0


def _check(hr, what):
    hr = int(hr)
    if hr < 0:
        raise OSError("%s failed (hr=0x%08X)" % (what, hr & 0xFFFFFFFF))
    return hr


def IUnknown_AddRef(punk):
    return int(_vcall(punk, 1, "I" if _use_ffi else ULONG, () if _use_ffi else ()))


def IUnknown_Release(punk):
    if not punk:
        return 0
    return int(_vcall(punk, 2, "I" if _use_ffi else ULONG, () if _use_ffi else ()))


def CoInitializeEx(flags=COINIT_APARTMENTTHREADED):
    if _use_ffi:
        hr = int(_raw_CoInitializeEx(None, int(flags)))
    else:
        hr = int(ole32.CoInitializeEx(None, int(flags)))
    if hr in (S_OK, S_FALSE):
        return hr
    if hr & 0xFFFFFFFF == RPC_E_CHANGED_MODE:
        return hr
    _check(hr, "CoInitializeEx")
    return hr


def CoUninitialize():
    if _use_ffi:
        _raw_CoUninitialize()
    else:
        ole32.CoUninitialize()


def CoCreateInstance(clsid, iid):
    if _use_ffi:
        obj_buf = bytearray(_PTR_SIZE)
        clsid_buf = clsid._buf if hasattr(clsid, "_buf") else clsid
        iid_buf = iid._buf if hasattr(iid, "_buf") else iid
        _check(
            _raw_CoCreateInstance(clsid_buf, None, CLSCTX_ALL, iid_buf, obj_buf),
            "CoCreateInstance",
        )
        return _ptr_read(uctypes.addressof(obj_buf))
    obj = c_void_p()
    _check(
        ole32.CoCreateInstance(byref(clsid), None, CLSCTX_ALL, byref(iid), byref(obj)),
        "CoCreateInstance",
    )
    return obj.value


def MMDeviceEnumerator_Create():
    return CoCreateInstance(CLSID_MMDeviceEnumerator, IID_IMMDeviceEnumerator)


def IMMDeviceEnumerator_GetDefaultAudioEndpoint(enumerator, data_flow, role=eConsole):
    if _use_ffi:
        device_buf = bytearray(_PTR_SIZE)
        _check(
            _vcall(
                enumerator,
                4,
                "i",
                "iip",
                int(data_flow),
                int(role),
                device_buf,
            ),
            "GetDefaultAudioEndpoint",
        )
        return _ptr_read(uctypes.addressof(device_buf))
    device = c_void_p()
    _check(
        _vcall(
            enumerator,
            4,
            HRESULT,
            (INT, INT, POINTER(c_void_p)),
            int(data_flow),
            int(role),
            byref(device),
        ),
        "GetDefaultAudioEndpoint",
    )
    return device.value


def IMMDevice_Activate_IAudioClient(device):
    if _use_ffi:
        client_buf = bytearray(_PTR_SIZE)
        _check(
            _vcall(
                device,
                3,
                "i",
                "pIpp",
                IID_IAudioClient._buf,
                CLSCTX_ALL,
                None,
                client_buf,
            ),
            "IMMDevice.Activate",
        )
        return _ptr_read(uctypes.addressof(client_buf))
    client = c_void_p()
    _check(
        _vcall(
            device,
            3,
            HRESULT,
            (POINTER(GUID), DWORD, LPVOID, POINTER(c_void_p)),
            byref(IID_IAudioClient),
            CLSCTX_ALL,
            None,
            byref(client),
        ),
        "IMMDevice.Activate",
    )
    return client.value


def WAVEFORMATEX_pcm(rate, channels, bits):
    fmt = WAVEFORMATEX()
    fmt.wFormatTag = WAVE_FORMAT_PCM
    fmt.nChannels = int(channels)
    fmt.nSamplesPerSec = int(rate)
    fmt.wBitsPerSample = int(bits)
    fmt.nBlockAlign = int(channels) * (int(bits) // 8)
    fmt.nAvgBytesPerSec = int(rate) * fmt.nBlockAlign
    fmt.cbSize = 0
    return fmt


def IAudioClient_Initialize_shared_pcm(client, fmt, buffer_ms):
    hns = max(10000, int(buffer_ms) * 10000)
    flags = AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM | AUDCLNT_STREAMFLAGS_SRC_DEFAULT_QUALITY
    if _use_ffi:
        fmt_buf = fmt._buf if hasattr(fmt, "_buf") else fmt
        _check(
            _vcall(
                client,
                3,
                "i",
                "iIqqpp",
                AUDCLNT_SHAREMODE_SHARED,
                flags,
                hns,
                0,
                fmt_buf,
                None,
            ),
            "IAudioClient.Initialize",
        )
        return
    _check(
        _vcall(
            client,
            3,
            HRESULT,
            (INT, DWORD, INT64, INT64, POINTER(WAVEFORMATEX), LPVOID),
            AUDCLNT_SHAREMODE_SHARED,
            flags,
            hns,
            0,
            byref(fmt),
            None,
        ),
        "IAudioClient.Initialize",
    )


def IAudioClient_GetBufferSize(client):
    if _use_ffi:
        frames_buf = bytearray(4)
        _check(
            _vcall(client, 4, "i", "p", frames_buf),
            "IAudioClient.GetBufferSize",
        )
        return struct.unpack("<I", frames_buf)[0]
    frames = UINT32()
    _check(
        _vcall(client, 4, HRESULT, (POINTER(UINT32),), byref(frames)),
        "IAudioClient.GetBufferSize",
    )
    return int(frames.value)


def IAudioClient_GetCurrentPadding(client):
    if _use_ffi:
        frames_buf = bytearray(4)
        _check(
            _vcall(client, 6, "i", "p", frames_buf),
            "IAudioClient.GetCurrentPadding",
        )
        return struct.unpack("<I", frames_buf)[0]
    frames = UINT32()
    _check(
        _vcall(client, 6, HRESULT, (POINTER(UINT32),), byref(frames)),
        "IAudioClient.GetCurrentPadding",
    )
    return int(frames.value)


def IAudioClient_Start(client):
    _check(_vcall(client, 10, "i" if _use_ffi else HRESULT, () if _use_ffi else ()), "IAudioClient.Start")


def IAudioClient_Stop(client):
    hr = int(_vcall(client, 11, "i" if _use_ffi else HRESULT, () if _use_ffi else ()))
    if hr < 0:
        raise OSError("IAudioClient.Stop failed (hr=0x%08X)" % (hr & 0xFFFFFFFF))


def IAudioClient_Reset(client):
    _vcall(client, 12, "i" if _use_ffi else HRESULT, () if _use_ffi else ())


def IAudioClient_GetService(client, iid):
    if _use_ffi:
        svc_buf = bytearray(_PTR_SIZE)
        iid_buf = iid._buf if hasattr(iid, "_buf") else iid
        _check(
            _vcall(
                client,
                14,
                "i",
                "pp",
                iid_buf,
                svc_buf,
            ),
            "IAudioClient.GetService",
        )
        return _ptr_read(uctypes.addressof(svc_buf))
    svc = c_void_p()
    _check(
        _vcall(
            client,
            14,
            HRESULT,
            (POINTER(GUID), POINTER(c_void_p)),
            byref(iid),
            byref(svc),
        ),
        "IAudioClient.GetService",
    )
    return svc.value


def IAudioRenderClient_GetBuffer(render, frames):
    if _use_ffi:
        data_buf = bytearray(_PTR_SIZE)
        _check(
            _vcall(
                render,
                3,
                "i",
                "Ip",
                int(frames),
                data_buf,
            ),
            "IAudioRenderClient.GetBuffer",
        )
        return _ptr_read(uctypes.addressof(data_buf))
    data = c_void_p()
    _check(
        _vcall(
            render,
            3,
            HRESULT,
            (UINT32, POINTER(c_void_p)),
            UINT32(int(frames)),
            byref(data),
        ),
        "IAudioRenderClient.GetBuffer",
    )
    return data.value


def IAudioRenderClient_ReleaseBuffer(render, frames, flags=0):
    if _use_ffi:
        _check(
            _vcall(render, 4, "i", "II", int(frames), int(flags)),
            "IAudioRenderClient.ReleaseBuffer",
        )
        return
    _check(
        _vcall(render, 4, HRESULT, (UINT32, DWORD), UINT32(int(frames)), DWORD(int(flags))),
        "IAudioRenderClient.ReleaseBuffer",
    )


def IAudioCaptureClient_GetNextPacketSize(capture):
    if _use_ffi:
        frames_buf = bytearray(4)
        _check(
            _vcall(capture, 5, "i", "p", frames_buf),
            "IAudioCaptureClient.GetNextPacketSize",
        )
        return struct.unpack("<I", frames_buf)[0]
    frames = UINT32()
    _check(
        _vcall(capture, 5, HRESULT, (POINTER(UINT32),), byref(frames)),
        "IAudioCaptureClient.GetNextPacketSize",
    )
    return int(frames.value)


def IAudioCaptureClient_GetBuffer(capture):
    if _use_ffi:
        data_buf = bytearray(_PTR_SIZE)
        frames_buf = bytearray(4)
        flags_buf = bytearray(4)
        _check(
            _vcall(
                capture,
                3,
                "i",
                "pppp",
                data_buf,
                frames_buf,
                flags_buf,
                None,
            ),
            "IAudioCaptureClient.GetBuffer",
        )
        return (
            _ptr_read(uctypes.addressof(data_buf)),
            struct.unpack("<I", frames_buf)[0],
            struct.unpack("<I", flags_buf)[0],
        )
    data = c_void_p()
    frames = UINT32()
    flags = DWORD()
    _check(
        _vcall(
            capture,
            3,
            HRESULT,
            (POINTER(c_void_p), POINTER(UINT32), POINTER(DWORD), LPVOID, LPVOID),
            byref(data),
            byref(frames),
            byref(flags),
            None,
            None,
        ),
        "IAudioCaptureClient.GetBuffer",
    )
    return data.value, int(frames.value), int(flags.value)


def IAudioCaptureClient_ReleaseBuffer(capture, frames):
    if _use_ffi:
        _check(
            _vcall(capture, 4, "i", "I", int(frames)),
            "IAudioCaptureClient.ReleaseBuffer",
        )
        return
    _check(
        _vcall(capture, 4, HRESULT, (UINT32,), UINT32(int(frames))),
        "IAudioCaptureClient.ReleaseBuffer",
    )
