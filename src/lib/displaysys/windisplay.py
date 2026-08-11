# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.windisplay — Win32 HWND display driver (CPython on Windows).
"""

import struct
import sys

import uwin32 as win

from displaysys import (
    _DESKTOP_WINDOW_CHROME_H,
    _DESKTOP_WINDOW_CHROME_W,
    DisplayDriver,
    color_rgb,
    desktop_work_area,
    fit_scale_to_desktop,
    notify_board_config_scale_override,
)
import events
import keys

__all__ = ["WinDisplay", "get_events", "poll_event"]

_CLASS_NAME = "PyDevicesWinDisplay"
_displays = []
_hwnd_map = {}
_pending = []
_wndproc_ref = None
_class_registered = False


def _color565_bytes(c):
    c = int(c) & 0xFFFF
    return bytes((c & 0xFF, c >> 8))


def _rgb565_to_bgra_row(src, dst, width):
    for x in range(width):
        lo = src[x * 2]
        hi = src[x * 2 + 1]
        r = hi & 0xF8 | (hi >> 5) & 0x07
        g = (hi << 5) & 0xE0 | (lo >> 3) & 0x1F
        b = (lo << 3) & 0xF8 | (lo >> 2) & 0x07
        o = x * 4
        dst[o] = b
        dst[o + 1] = g
        dst[o + 2] = r
        dst[o + 3] = 255


def _rotate_rgb565(buf, width, height, angle):
    """Return (new_buf, new_w, new_h) after rotating *angle* degrees clockwise."""
    angle %= 360
    if angle == 0:
        return buf, width, height
    src = memoryview(buf)
    if angle == 180:
        out = bytearray(len(buf))
        n = width * height
        for i in range(n):
            j = n - 1 - i
            out[j * 2 : j * 2 + 2] = src[i * 2 : i * 2 + 2]
        return out, width, height
    out_w, out_h = height, width
    out = bytearray(out_w * out_h * 2)
    if angle == 90:
        for y in range(height):
            for x in range(width):
                nx, ny = height - 1 - y, x
                di = (ny * out_w + nx) * 2
                si = (y * width + x) * 2
                out[di : di + 2] = src[si : si + 2]
    else:  # 270
        for y in range(height):
            for x in range(width):
                nx, ny = y, width - 1 - x
                di = (ny * out_w + nx) * 2
                si = (y * width + x) * 2
                out[di : di + 2] = src[si : si + 2]
    return out, out_w, out_h


def _display_for_hwnd(hwnd):
    return _hwnd_map.get(win.hwnd_int(hwnd))


def _handle_close(display):
    if display is None or display is _displays[0] or len(_displays) <= 1:
        return events.Quit(events.QUIT)
    runtime = getattr(display, "runtime", None)
    if runtime is not None and callable(getattr(runtime, "remove_display", None)):
        runtime.remove_display(display)
    else:
        try:
            display.quit()
        except Exception:
            pass
    return None


def _mouse_buttons(wparam):
    l = 1 if wparam & win.MK_LBUTTON else 0
    r = 1 if wparam & win.MK_RBUTTON else 0
    m = 1 if wparam & win.MK_MBUTTON else 0
    return (l, m, r)


def _queue(evt):
    if evt is not None:
        _pending.append(evt)


def _wndproc(hwnd, msg, wparam, lparam):
    display = _display_for_hwnd(hwnd)
    wid = win.hwnd_int(hwnd)
    if msg == win.WM_PAINT:
        hdc, ps = win.BeginPaint(hwnd)
        try:
            if display is not None:
                display._present(hdc)
        finally:
            win.EndPaint(hwnd, ps)
        return 0
    if msg == win.WM_CLOSE:
        _queue(_handle_close(display))
        return 0
    if msg == win.WM_DESTROY:
        return 0
    if msg == win.WM_MOUSEMOVE:
        x, y = win.GET_X_LPARAM(lparam), win.GET_Y_LPARAM(lparam)
        rel = (0, 0)
        if display is not None:
            px, py = getattr(display, "_last_mouse", (x, y))
            rel = (x - px, y - py)
            display._last_mouse = (x, y)
        _queue(events.Motion(events.MOUSEMOTION, (x, y), rel, _mouse_buttons(wparam), False, wid))
        return 0
    if msg in (win.WM_LBUTTONDOWN, win.WM_MBUTTONDOWN, win.WM_RBUTTONDOWN):
        button = {win.WM_LBUTTONDOWN: 1, win.WM_MBUTTONDOWN: 2, win.WM_RBUTTONDOWN: 3}[msg]
        x, y = win.GET_X_LPARAM(lparam), win.GET_Y_LPARAM(lparam)
        _queue(events.Button(events.MOUSEBUTTONDOWN, (x, y), button, False, wid))
        return 0
    if msg in (win.WM_LBUTTONUP, win.WM_MBUTTONUP, win.WM_RBUTTONUP):
        button = {win.WM_LBUTTONUP: 1, win.WM_MBUTTONUP: 2, win.WM_RBUTTONUP: 3}[msg]
        x, y = win.GET_X_LPARAM(lparam), win.GET_Y_LPARAM(lparam)
        _queue(events.Button(events.MOUSEBUTTONUP, (x, y), button, False, wid))
        return 0
    if msg in (win.WM_MOUSEWHEEL, win.WM_MOUSEHWHEEL):
        delta = win.GET_WHEEL_DELTA_WPARAM(wparam) / float(win.WHEEL_DELTA)
        sx = win.GET_X_LPARAM(lparam)
        sy = win.GET_Y_LPARAM(lparam)
        if display is not None and display._hwnd:
            sx, sy = win.ScreenToClient(display._hwnd, sx, sy)
        if msg == win.WM_MOUSEWHEEL:
            _queue(events.Wheel(events.MOUSEWHEEL, False, 0, delta, 0.0, delta, False, wid))
        else:
            _queue(events.Wheel(events.MOUSEWHEEL, False, delta, 0, delta, 0.0, False, wid))
        return 0
    if msg in (win.WM_KEYDOWN, win.WM_KEYUP, win.WM_SYSKEYDOWN, win.WM_SYSKEYUP):
        repeat = bool(lparam & 0x40000000) and msg in (win.WM_KEYDOWN, win.WM_SYSKEYDOWN)
        if repeat:
            return 0
        vk = int(wparam) & 0xFF
        key = win.virtual_key_to_sdl(vk)
        name = keys.keyname(key)
        if name == "Unknown":
            name = win.GetKeyNameTextW(lparam) or str(vk)
        et = events.KEYDOWN if msg in (win.WM_KEYDOWN, win.WM_SYSKEYDOWN) else events.KEYUP
        _queue(events.Key(et, name, key, win.modifier_mask(), vk, wid))
        return 0
    return win.DefWindowProcW(hwnd, msg, wparam, lparam)


def _ensure_class():
    global _wndproc_ref, _class_registered
    if _class_registered:
        return
    _wndproc_ref = win.WNDPROC(_wndproc)
    cls = win.WNDCLASSEXW()
    cls.cbSize = win.sizeof(win.WNDCLASSEXW)
    cls.style = win.CS_HREDRAW | win.CS_VREDRAW
    cls.lpfnWndProc = _wndproc_ref
    cls.hInstance = win.GetModuleHandleW()
    cls.hCursor = win.LoadCursorW(None, win.IDC_ARROW)
    cls.hbrBackground = win.COLOR_WINDOW + 1
    cls.lpszClassName = _CLASS_NAME
    win.RegisterClassExW(cls)
    _class_registered = True


def _pump():
    while True:
        msg = win.PeekMessageW()
        if msg is None:
            break
        if msg.message == win.WM_QUIT:
            _queue(events.Quit(events.QUIT))
            continue
        win.TranslateMessage(msg)
        win.DispatchMessageW(msg)


def poll_event():
    _pump()
    if not _pending:
        return None
    return _pending.pop(0)


def get_events():
    _pump()
    if not _pending:
        return None
    out = list(_pending)
    del _pending[:]
    return out


class WinDisplay(DisplayDriver):
    """Emulate an LCD window with a Win32 HWND (via ``uwin32``).

    Logical framebuffer is RGB565. ``show()`` converts scroll bands to BGRA
    and ``StretchDIBits`` into the client area.
    """

    needs_refresh = True
    requires_async_timer = False
    quit_chord = (keys.K_q, keys.KMOD_CTRL)

    def __init__(
        self,
        width=320,
        height=240,
        rotation=0,
        color_depth=16,
        title="Win32 Display",
        scale=1.0,
        x=None,
        y=None,
        *,
        quiet=False,
    ):
        if color_depth != 16:
            raise ValueError("WinDisplay only supports color_depth=16")
        self._width = width
        self._height = height
        self._rotation = rotation
        self.color_depth = color_depth
        self._title = title
        self._scale = scale
        self.touch_scale = scale
        self._requires_byteswap = False
        self._hwnd = None
        self._window_id = None
        self.runtime = None
        self._render_dirty = False
        self._last_mouse = (0, 0)
        self._bytes_per_pixel = 2
        self._buffer = bytearray(self._width * self._height * 2)
        self._visible = bytearray(self._width * self._height * 2)
        self._bgra = bytearray(self._width * self._height * 4)
        self._bmi = None
        win.CoInitializeEx()
        ux, uy, desktop_w, desktop_h = desktop_work_area()
        self._work_area = (ux, uy, desktop_w, desktop_h)
        requested_scale = self._scale
        fitted = fit_scale_to_desktop(
            self.width,
            self.height,
            requested_scale,
            desktop_w,
            desktop_h,
            chrome_w=_DESKTOP_WINDOW_CHROME_W,
            chrome_h=_DESKTOP_WINDOW_CHROME_H,
        )
        notify_board_config_scale_override("WinDisplay", requested_scale, fitted, quiet=quiet)
        if fitted != requested_scale:
            self._scale = fitted
            self.touch_scale = fitted
        self._place_x = x
        self._place_y = y
        super().__init__(quiet=quiet)
        self.touch_scale = self._scale
        self.get_events = get_events
        if self not in _displays:
            _displays.append(self)

    def init(self):
        _ensure_class()
        win_w = int(self.width * self._scale)
        win_h = int(self.height * self._scale)
        outer_w, outer_h = win.AdjustWindowRectEx(win_w, win_h, win.WS_DISPLAY)
        ux, uy, uw, uh = self._work_area
        if self._place_x is None or self._place_y is None:
            if uw > 0 and uh > 0:
                x = ux + max(0, (uw - outer_w) // 2)
                y = (
                    uy
                    + _DESKTOP_WINDOW_CHROME_H
                    + max(0, (uh - _DESKTOP_WINDOW_CHROME_H - outer_h) // 2)
                )
            else:
                x = y = win.CW_USEDEFAULT
        else:
            x, y = int(self._place_x), int(self._place_y)
        if self._hwnd is None:
            self._hwnd = win.CreateWindowExW(
                0,
                _CLASS_NAME,
                self._title,
                win.WS_DISPLAY,
                x,
                y,
                outer_w,
                outer_h,
            )
            self._window_id = win.hwnd_int(self._hwnd)
            _hwnd_map[self._window_id] = self
            win.ShowWindow(self._hwnd)
        else:
            win.SetWindowPos(self._hwnd, x, y, outer_w, outer_h)
        self._bmi = win.bmi_bgra(self.width, self.height)
        nbytes = self.width * self.height * 2
        if len(self._buffer) != nbytes:
            self._buffer = bytearray(nbytes)
            self._visible = bytearray(nbytes)
            self._bgra = bytearray(self.width * self.height * 4)
        super().vscrdef(0, self.height, 0)
        self.vscsad(False)

    def blit_rect(self, buffer, x, y, w, h):
        pitch = w * 2
        need = pitch * h
        buflen = len(buffer)
        if buflen < need:
            raise ValueError("Buffer size does not match dimensions")
        src = memoryview(buffer)[:need]
        dst = memoryview(self._buffer)
        dst_pitch = self.width * 2
        for row in range(h):
            s = row * pitch
            d = ((y + row) * dst_pitch) + (x * 2)
            dst[d : d + pitch] = src[s : s + pitch]
        self._render_dirty = True
        return (x, y, w, h)

    def fill_rect(self, x, y, w, h, c):
        pix = _color565_bytes(c)
        dst = memoryview(self._buffer)
        pitch = self.width * 2
        row = pix * w
        for yy in range(y, y + h):
            d = yy * pitch + x * 2
            dst[d : d + w * 2] = row
        self._render_dirty = True
        return (x, y, w, h)

    def pixel(self, x, y, c):
        return self.blit_rect(bytearray(_color565_bytes(c)), x, y, 1, 1)

    def vscrdef(self, tfa, vsa, bfa):
        super().vscrdef(tfa, vsa, bfa)
        self._render_dirty = True

    def vscsad(self, vssa=None):
        if vssa is not None:
            super().vscsad(vssa)
            self._render_dirty = True
        return self._vssa

    def _rotation_helper(self, value):
        angle = (value % 360) - (self._rotation % 360)
        if angle == 0:
            return
        self._buffer, _new_w, _new_h = _rotate_rgb565(
            self._buffer, self.width, self.height, angle % 360
        )
        self._render_dirty = True

    def _compose_visible(self):
        w = self.width
        h = self.height
        pitch = w * 2
        src = memoryview(self._buffer)
        dst = memoryview(self._visible)
        y_start = self.vscsad()
        if not y_start:
            dst[:] = src
            return
        rows = []
        rows.extend(range(self._tfa))
        rows.extend(range(y_start, self._tfa + self._vsa))
        rows.extend(range(self._tfa, y_start))
        rows.extend(range(self._tfa + self._vsa, h))
        for i, src_y in enumerate(rows):
            dst[i * pitch : (i + 1) * pitch] = src[src_y * pitch : (src_y + 1) * pitch]

    def _fill_bgra(self):
        w = self.width
        h = self.height
        src = memoryview(self._visible)
        dst = memoryview(self._bgra)
        for y in range(h):
            _rgb565_to_bgra_row(
                src[y * w * 2 : (y + 1) * w * 2], dst[y * w * 4 : (y + 1) * w * 4], w
            )

    def render(self, renderRect=None):
        if self._hwnd is None:
            return
        self._compose_visible()
        self._fill_bgra()
        self._render_dirty = False

    def _present(self, hdc=None):
        if self._hwnd is None or self._bmi is None:
            return
        if self._render_dirty:
            self.render()
        own = hdc is None
        if own:
            hdc = win.GetDC(self._hwnd)
        try:
            dest_w = int(self.width * self._scale)
            dest_h = int(self.height * self._scale)
            win.StretchDIBits(
                hdc,
                dest_w,
                dest_h,
                self.width,
                self.height,
                bytes(self._bgra),
                self._bmi,
            )
        finally:
            if own and hdc:
                win.ReleaseDC(self._hwnd, hdc)

    def show(self, _timer=None):
        if self._hwnd is None:
            return
        self._present()

    def _deinit(self):
        hwnd = self._hwnd
        self._hwnd = None
        wid = self._window_id
        self._window_id = None
        self.runtime = None
        if wid:
            _hwnd_map.pop(wid, None)
        try:
            _displays.remove(self)
        except ValueError:
            pass
        if hwnd:
            try:
                win.DestroyWindow(hwnd)
            except Exception:
                pass
        self._buffer = None
        self._visible = None
        self._bgra = None
