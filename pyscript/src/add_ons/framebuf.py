# SPDX-FileCopyrightText: 2016 Damien P. George
# Copyright 2024-2026 Brad Barnett
# SPDX-License-Identifier: MIT

"""
framebuf.py - a pure-Python, drop-in replacement for MicroPython's built-in
``framebuf`` module (https://docs.micropython.org/en/latest/library/framebuf.html)
for use on CPython and CircuitPython.

This module intentionally mirrors MicroPython's C implementation
(``extmod/modframebuf.c``, by Damien P. George) as closely as possible:

- Same format constants, same method signatures, same return values (``None``
  for every drawing method; only ``pixel()`` without a color argument returns
  a value).
- No pydisplay extensions (no ``RGB888``, no ``Area`` return values, no
  ``arc``/``circle``/``blit_rect``/etc.) and no imports from ``graphics``.

For the pydisplay-flavored subclass that adds ``Area`` bounding boxes,
``RGB888``, extra shapes, and file I/O, see ``graphics.FrameBuffer``
(``graphics/_framebuf_plus.py``), which subclasses this module.
"""

try:
    from ulab import numpy as np
except ImportError:
    try:
        import numpy as np
    except ImportError:
        np = None


# Framebuf format constants (values match MicroPython's framebuf module):
MONO_VLSB = 0
MVLSB = 0
RGB565 = 1
GS4_HMSB = 2
MONO_HLSB = 3
MONO_HMSB = 4
GS2_HMSB = 5
GS8 = 6


class MVLSBFormat:
    """Single bit displays, vertically mapped (e.g. SSD1306 OLED)."""

    depth = 1

    @staticmethod
    def set_pixel(fb, x, y, color):
        index = (y >> 3) * fb._stride + x
        offset = y & 0x07
        fb._buffer[index] = (fb._buffer[index] & ~(0x01 << offset) & 0xFF) | (
            (color != 0) << offset
        )

    @staticmethod
    def get_pixel(fb, x, y):
        index = (y >> 3) * fb._stride + x
        offset = y & 0x07
        return (fb._buffer[index] >> offset) & 0x01

    @staticmethod
    def fill_rect(fb, x, y, width, height, color):
        while height > 0:
            index = (y >> 3) * fb._stride + x
            offset = y & 0x07
            for w_w in range(width):
                fb._buffer[index + w_w] = (fb._buffer[index + w_w] & ~(0x01 << offset) & 0xFF) | (
                    (color != 0) << offset
                )
            y += 1
            height -= 1


class MHLSBFormat:
    """Single bit displays, horizontally mapped, bit 0 = rightmost pixel (e.g. PBM)."""

    depth = 1

    @staticmethod
    def set_pixel(fb, x, y, color):
        index = (x + y * fb._stride) >> 3
        offset = 7 - (x & 0x07)
        fb._buffer[index] = (fb._buffer[index] & ~(0x01 << offset) & 0xFF) | (
            (color != 0) << offset
        )

    @staticmethod
    def get_pixel(fb, x, y):
        index = (x + y * fb._stride) >> 3
        offset = 7 - (x & 0x07)
        return (fb._buffer[index] >> offset) & 0x01

    @staticmethod
    def fill_rect(fb, x, y, width, height, color):
        advance = fb._stride >> 3
        col = 1 if color else 0
        while width:
            index = (x >> 3) + y * advance
            offset = 7 - (x & 0x07)
            bit = 0x01 << offset
            for _ in range(height):
                fb._buffer[index] = (fb._buffer[index] & ~bit & 0xFF) | (col << offset)
                index += advance
            x += 1
            width -= 1


class MHMSBFormat:
    """Single bit displays, horizontally mapped, bit 0 = leftmost pixel."""

    depth = 1

    @staticmethod
    def set_pixel(fb, x, y, color):
        index = (x + y * fb._stride) >> 3
        offset = x & 0x07
        fb._buffer[index] = (fb._buffer[index] & ~(0x01 << offset) & 0xFF) | (
            (color != 0) << offset
        )

    @staticmethod
    def get_pixel(fb, x, y):
        index = (x + y * fb._stride) >> 3
        offset = x & 0x07
        return (fb._buffer[index] >> offset) & 0x01

    @staticmethod
    def fill_rect(fb, x, y, width, height, color):
        advance = fb._stride >> 3
        col = 1 if color else 0
        while width:
            index = (x >> 3) + y * advance
            offset = x & 0x07
            bit = 0x01 << offset
            for _ in range(height):
                fb._buffer[index] = (fb._buffer[index] & ~bit & 0xFF) | (col << offset)
                index += advance
            x += 1
            width -= 1


class GS2HMSBFormat:
    """2-bit grayscale, horizontally mapped MSB-first (e.g. HT16K33 8x8 Matrix)."""

    depth = 2

    @staticmethod
    def set_pixel(fb, x, y, color):
        index = (x + y * fb._stride) >> 2
        pixel = fb._buffer[index]
        shift = (x & 0b11) << 1
        mask = 0b11 << shift
        color = (color & 0b11) << shift
        fb._buffer[index] = color | (pixel & (~mask & 0xFF))

    @staticmethod
    def get_pixel(fb, x, y):
        index = (x + y * fb._stride) >> 2
        pixel = fb._buffer[index]
        shift = (x & 0b11) << 1
        return (pixel >> shift) & 0b11

    @staticmethod
    def fill_rect(fb, x, y, width, height, color):
        for _x in range(x, x + width):
            for _y in range(y, y + height):
                GS2HMSBFormat.set_pixel(fb, _x, _y, color)


class GS4HMSBFormat:
    """4-bit grayscale, horizontally mapped, two pixels per byte."""

    depth = 4

    @staticmethod
    def set_pixel(fb, x, y, color):
        index = (x + y * fb._stride) >> 1
        if x & 0x01:
            fb._buffer[index] = (color & 0x0F) | (fb._buffer[index] & 0xF0)
        else:
            fb._buffer[index] = ((color & 0x0F) << 4) | (fb._buffer[index] & 0x0F)

    @staticmethod
    def get_pixel(fb, x, y):
        index = (x + y * fb._stride) >> 1
        if x & 0x01:
            return fb._buffer[index] & 0x0F
        return fb._buffer[index] >> 4

    @staticmethod
    def fill_rect(fb, x, y, width, height, color):
        for _y in range(y, y + height):
            for _x in range(x, x + width):
                GS4HMSBFormat.set_pixel(fb, _x, _y, color)


class GS8Format:
    """8-bit grayscale/palette, one byte per pixel."""

    depth = 8

    @staticmethod
    def set_pixel(fb, x, y, color):
        fb._buffer[y * fb._stride + x] = color & 0xFF

    @staticmethod
    def get_pixel(fb, x, y):
        return fb._buffer[y * fb._stride + x]

    @staticmethod
    def fill_rect(fb, x, y, width, height, color):
        row = bytes((color & 0xFF,)) * width
        for _y in range(y, y + height):
            index = _y * fb._stride + x
            fb._buffer[index : index + width] = row


class RGB565Format:
    """16-bit color, two bytes per pixel, little-endian."""

    depth = 16

    @staticmethod
    def set_pixel(fb, x, y, color):
        index = (x + y * fb._stride) * 2
        fb._buffer[index : index + 2] = (color & 0xFFFF).to_bytes(2, "little")

    @staticmethod
    def get_pixel(fb, x, y):
        index = (x + y * fb._stride) * 2
        return int.from_bytes(fb._buffer[index : index + 2], "little")

    @staticmethod
    def fill_rect(fb, x, y, width, height, color):
        stride = fb._stride
        rgb565_color = (color & 0xFFFF).to_bytes(2, "little")
        if np:
            rgb565_color_int = int.from_bytes(rgb565_color, "little")
            arr = np.frombuffer(fb._buffer, dtype=np.uint16)
            for _y in range(y, y + height):
                arr[_y * stride + x : _y * stride + x + width] = rgb565_color_int
        else:
            for _y in range(y, y + height):
                offset = _y * stride
                for _x in range(x, x + width):
                    index = (offset + _x) * 2
                    fb._buffer[index : index + 2] = rgb565_color


def _setpixel_checked(fb, x, y, color, mask):
    if mask and 0 <= x < fb._width and 0 <= y < fb._height:
        fb._format.set_pixel(fb, x, y, color)


def _fill_rect(fb, x, y, w, h, color):
    """Clip ``x, y, w, h`` to the framebuffer bounds, then delegate to the format."""
    if h < 1 or w < 1 or x + w <= 0 or y + h <= 0 or y >= fb._height or x >= fb._width:
        return
    xend = min(fb._width, x + w)
    yend = min(fb._height, y + h)
    x = max(x, 0)
    y = max(y, 0)
    fb._format.fill_rect(fb, x, y, xend - x, yend - y, color)


def _line(fb, x1, y1, x2, y2, c):
    dx = x2 - x1
    if dx > 0:
        sx = 1
    else:
        dx = -dx
        sx = -1

    dy = y2 - y1
    if dy > 0:
        sy = 1
    else:
        dy = -dy
        sy = -1

    steep = dy > dx
    if steep:
        x1, y1 = y1, x1
        dx, dy = dy, dx
        sx, sy = sy, sx

    e = 2 * dy - dx
    for _ in range(dx):
        if steep:
            if 0 <= y1 < fb._width and 0 <= x1 < fb._height:
                fb._format.set_pixel(fb, y1, x1, c)
        else:
            if 0 <= x1 < fb._width and 0 <= y1 < fb._height:
                fb._format.set_pixel(fb, x1, y1, c)
        while e >= 0:
            y1 += sy
            e -= 2 * dx
        x1 += sx
        e += 2 * dy

    _setpixel_checked(fb, x2, y2, c, 1)


_ELLIPSE_MASK_FILL = 0x10
_ELLIPSE_MASK_ALL = 0x0F


def _draw_ellipse_points(fb, cx, cy, x, y, c, mask):
    if mask & _ELLIPSE_MASK_FILL:
        if mask & 0x1:
            _fill_rect(fb, cx, cy - y, x + 1, 1, c)
        if mask & 0x2:
            _fill_rect(fb, cx - x, cy - y, x + 1, 1, c)
        if mask & 0x4:
            _fill_rect(fb, cx - x, cy + y, x + 1, 1, c)
        if mask & 0x8:
            _fill_rect(fb, cx, cy + y, x + 1, 1, c)
    else:
        _setpixel_checked(fb, cx + x, cy - y, c, mask & 0x1)
        _setpixel_checked(fb, cx - x, cy - y, c, mask & 0x2)
        _setpixel_checked(fb, cx - x, cy + y, c, mask & 0x4)
        _setpixel_checked(fb, cx + x, cy + y, c, mask & 0x8)


def _ellipse(fb, cx, cy, xr, yr, c, f=False, m=_ELLIPSE_MASK_ALL):
    mask = (_ELLIPSE_MASK_FILL if f else 0) | (m & _ELLIPSE_MASK_ALL)
    if xr == 0 and yr == 0:
        _setpixel_checked(fb, cx, cy, c, mask & _ELLIPSE_MASK_ALL)
        return

    two_asquare = 2 * xr * xr
    two_bsquare = 2 * yr * yr
    x = xr
    y = 0
    xchange = yr * yr * (1 - 2 * xr)
    ychange = xr * xr
    ellipse_error = 0
    stoppingx = two_bsquare * xr
    stoppingy = 0
    while stoppingx >= stoppingy:
        _draw_ellipse_points(fb, cx, cy, x, y, c, mask)
        y += 1
        stoppingy += two_asquare
        ellipse_error += ychange
        ychange += two_asquare
        if (2 * ellipse_error + xchange) > 0:
            x -= 1
            stoppingx -= two_bsquare
            ellipse_error += xchange
            xchange += two_bsquare

    x = 0
    y = yr
    xchange = yr * yr
    ychange = xr * xr * (1 - 2 * yr)
    ellipse_error = 0
    stoppingx = 0
    stoppingy = two_asquare * yr
    while stoppingx <= stoppingy:
        _draw_ellipse_points(fb, cx, cy, x, y, c, mask)
        x += 1
        stoppingx += two_bsquare
        ellipse_error += xchange
        xchange += two_bsquare
        if (2 * ellipse_error + ychange) > 0:
            y -= 1
            stoppingy -= two_asquare
            ellipse_error += ychange
            ychange += two_asquare


def _trunc_div(a, b):
    """Integer division truncated toward zero, matching C's ``/`` for ints."""
    q = a // b
    if (a % b != 0) and ((a < 0) != (b < 0)):
        q += 1
    return q


def _poly_points(coords):
    """Normalize ``coords`` (a flat array/list of ints, or a list of (x, y) pairs)."""
    coords = list(coords)
    if coords and isinstance(coords[0], (list, tuple)):
        return [(int(px), int(py)) for px, py in coords]
    if len(coords) % 2:
        coords = coords[:-1]
    return [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]


def _poly_edges(pts):
    """Yield (px1, py1, px2, py2) edges in the exact order MicroPython visits them:
    point[0] -> point[n-1] -> point[n-2] -> ... -> point[1] -> point[0].

    Line drawing is not always symmetric under endpoint reversal for steep
    segments (integer rounding), so this order must match ``modframebuf.c``
    exactly for pixel-identical output.
    """
    px1, py1 = pts[0]
    for k in range(len(pts) - 1, -1, -1):
        px2, py2 = pts[k]
        yield px1, py1, px2, py2
        px1, py1 = px2, py2


def _poly(fb, x, y, coords, c, f=False):
    pts = _poly_points(coords)
    if not pts:
        return
    edges = list(_poly_edges(pts))

    if f:
        y_min = min(p[1] for p in pts)
        y_max = max(p[1] for p in pts)
        for row in range(y_min, y_max + 1):
            nodes = []
            for px1, py1, px2, py2 in edges:
                if py1 != py2 and ((py1 > row and py2 <= row) or (py1 <= row and py2 > row)):
                    node = _trunc_div(
                        32 * px1 + _trunc_div(32 * (px2 - px1) * (row - py1), py2 - py1) + 16,
                        32,
                    )
                    nodes.append(node)
                elif row == max(py1, py2):
                    if py1 < py2:
                        _setpixel_checked(fb, x + px2, y + py2, c, 1)
                    elif py2 < py1:
                        _setpixel_checked(fb, x + px1, y + py1, c, 1)
                    else:
                        _line(fb, x + px1, y + py1, x + px2, y + py2, c)
            if not nodes:
                continue
            nodes.sort()
            for i in range(0, len(nodes) - 1, 2):
                _fill_rect(fb, x + nodes[i], y + row, nodes[i + 1] - nodes[i] + 1, 1, c)
    else:
        for px1, py1, px2, py2 in edges:
            _line(fb, x + px1, y + py1, x + px2, y + py2, c)


def _scroll(fb, xstep, ystep):
    width = fb._width
    height = fb._height

    if xstep < 0:
        if -xstep >= width:
            return
        sx = 0
        xend = width + xstep
        dx = 1
    else:
        if xstep >= width:
            return
        sx = width - 1
        xend = xstep - 1
        dx = -1

    if ystep < 0:
        if -ystep >= height:
            return
        y = 0
        yend = height + ystep
        dy = 1
    else:
        if ystep >= height:
            return
        y = height - 1
        yend = ystep - 1
        dy = -1

    while y != yend:
        x = sx
        while x != xend:
            fb._format.set_pixel(fb, x, y, fb._format.get_pixel(fb, x - xstep, y - ystep))
            x += dx
        y += dy


def _as_readonly_framebuffer(arg):
    """Accept a ``FrameBuffer`` or a ``(buffer, width, height, format[, stride])`` tuple/list."""
    if hasattr(arg, "width") and hasattr(arg, "height") and hasattr(arg, "pixel"):
        return arg
    items = list(arg)
    if len(items) < 4 or len(items) > 5:
        raise ValueError("invalid framebuffer arguments")
    return FrameBuffer(*items)


def _blit(fb, source, x, y, key=-1, palette=None):
    source = _as_readonly_framebuffer(source)
    if palette is not None:
        palette = _as_readonly_framebuffer(palette)

    if x >= fb._width or y >= fb._height or -x >= source.width or -y >= source.height:
        return

    x0 = max(0, x)
    y0 = max(0, y)
    x1 = max(0, -x)
    y1 = max(0, -y)
    x0end = min(fb._width, x + source.width)
    y0end = min(fb._height, y + source.height)

    for cy0 in range(y0, y0end):
        cx1 = x1
        for cx0 in range(x0, x0end):
            col = source.pixel(cx1, y1)
            if palette is not None:
                col = palette.pixel(col, 0)
            if col != key:
                fb._format.set_pixel(fb, cx0, cy0, col)
            cx1 += 1
        y1 += 1


# font_petme128_8x8: 96 glyphs (ASCII 32-127), 8 bytes each. Each byte is one
# vertical column of 8 pixels with bit 0 at the top. Ported byte-for-byte from
# MicroPython's extmod/font_petme128_8x8.h (Damien P. George).
_FONT_PETME128_8X8 = (
    b"\x00\x00\x00\x00\x00\x00\x00\x00"  # 32=<space>
    b"\x00\x00\x00\x4f\x4f\x00\x00\x00"  # 33=!
    b"\x00\x07\x07\x00\x00\x07\x07\x00"  # 34="
    b"\x14\x7f\x7f\x14\x14\x7f\x7f\x14"  # 35=#
    b"\x00\x24\x2e\x6b\x6b\x3a\x12\x00"  # 36=$
    b"\x00\x63\x33\x18\x0c\x66\x63\x00"  # 37=%
    b"\x00\x32\x7f\x4d\x4d\x77\x72\x50"  # 38=&
    b"\x00\x00\x00\x04\x06\x03\x01\x00"  # 39='
    b"\x00\x00\x1c\x3e\x63\x41\x00\x00"  # 40=(
    b"\x00\x00\x41\x63\x3e\x1c\x00\x00"  # 41=)
    b"\x08\x2a\x3e\x1c\x1c\x3e\x2a\x08"  # 42=*
    b"\x00\x08\x08\x3e\x3e\x08\x08\x00"  # 43=+
    b"\x00\x00\x80\xe0\x60\x00\x00\x00"  # 44=,
    b"\x00\x08\x08\x08\x08\x08\x08\x00"  # 45=-
    b"\x00\x00\x00\x60\x60\x00\x00\x00"  # 46=.
    b"\x00\x40\x60\x30\x18\x0c\x06\x02"  # 47=/
    b"\x00\x3e\x7f\x49\x45\x7f\x3e\x00"  # 48=0
    b"\x00\x40\x44\x7f\x7f\x40\x40\x00"  # 49=1
    b"\x00\x62\x73\x51\x49\x4f\x46\x00"  # 50=2
    b"\x00\x22\x63\x49\x49\x7f\x36\x00"  # 51=3
    b"\x00\x18\x18\x14\x16\x7f\x7f\x10"  # 52=4
    b"\x00\x27\x67\x45\x45\x7d\x39\x00"  # 53=5
    b"\x00\x3e\x7f\x49\x49\x7b\x32\x00"  # 54=6
    b"\x00\x03\x03\x79\x7d\x07\x03\x00"  # 55=7
    b"\x00\x36\x7f\x49\x49\x7f\x36\x00"  # 56=8
    b"\x00\x26\x6f\x49\x49\x7f\x3e\x00"  # 57=9
    b"\x00\x00\x00\x24\x24\x00\x00\x00"  # 58=:
    b"\x00\x00\x80\xe4\x64\x00\x00\x00"  # 59=;
    b"\x00\x08\x1c\x36\x63\x41\x41\x00"  # 60=<
    b"\x00\x14\x14\x14\x14\x14\x14\x00"  # 61==
    b"\x00\x41\x41\x63\x36\x1c\x08\x00"  # 62=>
    b"\x00\x02\x03\x51\x59\x0f\x06\x00"  # 63=?
    b"\x00\x3e\x7f\x41\x4d\x4f\x2e\x00"  # 64=@
    b"\x00\x7c\x7e\x0b\x0b\x7e\x7c\x00"  # 65=A
    b"\x00\x7f\x7f\x49\x49\x7f\x36\x00"  # 66=B
    b"\x00\x3e\x7f\x41\x41\x63\x22\x00"  # 67=C
    b"\x00\x7f\x7f\x41\x63\x3e\x1c\x00"  # 68=D
    b"\x00\x7f\x7f\x49\x49\x41\x41\x00"  # 69=E
    b"\x00\x7f\x7f\x09\x09\x01\x01\x00"  # 70=F
    b"\x00\x3e\x7f\x41\x49\x7b\x3a\x00"  # 71=G
    b"\x00\x7f\x7f\x08\x08\x7f\x7f\x00"  # 72=H
    b"\x00\x00\x41\x7f\x7f\x41\x00\x00"  # 73=I
    b"\x00\x20\x60\x41\x7f\x3f\x01\x00"  # 74=J
    b"\x00\x7f\x7f\x1c\x36\x63\x41\x00"  # 75=K
    b"\x00\x7f\x7f\x40\x40\x40\x40\x00"  # 76=L
    b"\x00\x7f\x7f\x06\x0c\x06\x7f\x7f"  # 77=M
    b"\x00\x7f\x7f\x0e\x1c\x7f\x7f\x00"  # 78=N
    b"\x00\x3e\x7f\x41\x41\x7f\x3e\x00"  # 79=O
    b"\x00\x7f\x7f\x09\x09\x0f\x06\x00"  # 80=P
    b"\x00\x1e\x3f\x21\x61\x7f\x5e\x00"  # 81=Q
    b"\x00\x7f\x7f\x19\x39\x6f\x46\x00"  # 82=R
    b"\x00\x26\x6f\x49\x49\x7b\x32\x00"  # 83=S
    b"\x00\x01\x01\x7f\x7f\x01\x01\x00"  # 84=T
    b"\x00\x3f\x7f\x40\x40\x7f\x3f\x00"  # 85=U
    b"\x00\x1f\x3f\x60\x60\x3f\x1f\x00"  # 86=V
    b"\x00\x7f\x7f\x30\x18\x30\x7f\x7f"  # 87=W
    b"\x00\x63\x77\x1c\x1c\x77\x63\x00"  # 88=X
    b"\x00\x07\x0f\x78\x78\x0f\x07\x00"  # 89=Y
    b"\x00\x61\x71\x59\x4d\x47\x43\x00"  # 90=Z
    b"\x00\x00\x7f\x7f\x41\x41\x00\x00"  # 91=[
    b"\x00\x02\x06\x0c\x18\x30\x60\x40"  # 92=<backslash>
    b"\x00\x00\x41\x41\x7f\x7f\x00\x00"  # 93=]
    b"\x00\x08\x0c\x06\x06\x0c\x08\x00"  # 94=^
    b"\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0"  # 95=_
    b"\x00\x00\x01\x03\x06\x04\x00\x00"  # 96=`
    b"\x00\x20\x74\x54\x54\x7c\x78\x00"  # 97=a
    b"\x00\x7f\x7f\x44\x44\x7c\x38\x00"  # 98=b
    b"\x00\x38\x7c\x44\x44\x6c\x28\x00"  # 99=c
    b"\x00\x38\x7c\x44\x44\x7f\x7f\x00"  # 100=d
    b"\x00\x38\x7c\x54\x54\x5c\x58\x00"  # 101=e
    b"\x00\x08\x7e\x7f\x09\x03\x02\x00"  # 102=f
    b"\x00\x98\xbc\xa4\xa4\xfc\x7c\x00"  # 103=g
    b"\x00\x7f\x7f\x04\x04\x7c\x78\x00"  # 104=h
    b"\x00\x00\x00\x7d\x7d\x00\x00\x00"  # 105=i
    b"\x00\x40\xc0\x80\x80\xfd\x7d\x00"  # 106=j
    b"\x00\x7f\x7f\x30\x38\x6c\x44\x00"  # 107=k
    b"\x00\x00\x41\x7f\x7f\x40\x00\x00"  # 108=l
    b"\x00\x7c\x7c\x18\x30\x18\x7c\x7c"  # 109=m
    b"\x00\x7c\x7c\x04\x04\x7c\x78\x00"  # 110=n
    b"\x00\x38\x7c\x44\x44\x7c\x38\x00"  # 111=o
    b"\x00\xfc\xfc\x24\x24\x3c\x18\x00"  # 112=p
    b"\x00\x18\x3c\x24\x24\xfc\xfc\x00"  # 113=q
    b"\x00\x7c\x7c\x04\x04\x0c\x08\x00"  # 114=r
    b"\x00\x48\x5c\x54\x54\x74\x20\x00"  # 115=s
    b"\x04\x04\x3f\x7f\x44\x64\x20\x00"  # 116=t
    b"\x00\x3c\x7c\x40\x40\x7c\x3c\x00"  # 117=u
    b"\x00\x1c\x3c\x60\x60\x3c\x1c\x00"  # 118=v
    b"\x00\x1c\x7c\x30\x18\x30\x7c\x1c"  # 119=w
    b"\x00\x44\x6c\x38\x38\x6c\x44\x00"  # 120=x
    b"\x00\x9c\xbc\xa0\xa0\xfc\x7c\x00"  # 121=y
    b"\x00\x44\x64\x74\x5c\x4c\x44\x00"  # 122=z
    b"\x00\x08\x08\x3e\x77\x41\x41\x00"  # 123={
    b"\x00\x00\x00\xff\xff\x00\x00\x00"  # 124=|
    b"\x00\x41\x41\x77\x3e\x08\x08\x00"  # 125=}
    b"\x00\x02\x03\x01\x03\x02\x03\x01"  # 126=~
    b"\xaa\x55\xaa\x55\xaa\x55\xaa\x55"  # 127
)


def _text(fb, s, x0, y0, c=1):
    x = x0
    for ch in s:
        code = ord(ch)
        if code < 32 or code > 127:
            code = 127
        base = (code - 32) * 8
        for j in range(8):
            if 0 <= x < fb._width:
                vline_data = _FONT_PETME128_8X8[base + j]
                y = y0
                while vline_data:
                    if (vline_data & 1) and 0 <= y < fb._height:
                        fb._format.set_pixel(fb, x, y, c)
                    vline_data >>= 1
                    y += 1
            x += 1


class FrameBuffer:
    """
    FrameBuffer object.

    Args:
        buffer (bytearray): An object with a buffer protocol, large enough for
            every pixel defined by width, height and format.
        width (int): The width of the frame buffer in pixels.
        height (int): The height of the frame buffer in pixels.
        format (int): The format of the frame buffer. One of:
            - ``MONO_VLSB``: Single bit displays (like SSD1306 OLED)
            - ``MONO_HLSB``: Single bit files like PBM (Portable BitMap)
            - ``MONO_HMSB``: Single bit displays where the bits in a byte are horizontally mapped
                Each byte occupies 8 horizontal pixels with bit 0 being the leftmost.
            - ``RGB565``: 16-bit color displays
            - ``GS2_HMSB``: 2-bit color displays like the HT16K33 8x8 Matrix
            - ``GS4_HMSB``: 4-bit grayscale displays
            - ``GS8``: 8-bit grayscale/palette displays
        stride (int): The number of pixels between each horizontal line of the frame buffer
            If not given, it is assumed to be equal to the width.
    """

    def __init__(self, buffer, width, height, format, stride=None):
        if width < 1 or height < 1:
            raise ValueError("invalid width/height")
        self._buffer = buffer
        self._width = width
        self._height = height
        self._stride = stride if stride is not None else width
        if format == MONO_VLSB:
            self._format = MVLSBFormat()
        elif format == MONO_HLSB:
            self._stride = (self._stride + 7) & ~7
            self._format = MHLSBFormat()
        elif format == MONO_HMSB:
            self._stride = (self._stride + 7) & ~7
            self._format = MHMSBFormat()
        elif format == RGB565:
            self._format = RGB565Format()
        elif format == GS2_HMSB:
            self._stride = (self._stride + 3) & ~3
            self._format = GS2HMSBFormat()
        elif format == GS4_HMSB:
            self._stride = (self._stride + 1) & ~1
            self._format = GS4HMSBFormat()
        elif format == GS8:
            self._format = GS8Format()
        else:
            raise ValueError("invalid format")

    @property
    def width(self):
        """The width of the FrameBuffer in pixels."""
        return self._width

    @property
    def height(self):
        """The height of the FrameBuffer in pixels."""
        return self._height

    def fill(self, c):
        """Fill the entire FrameBuffer with the specified color.

        Equivalent to ``fill_rect(0, 0, width, height, c)`` (matching
        MicroPython, which has no separate per-format ``fill``).
        """
        _fill_rect(self, 0, 0, self._width, self._height, c)

    def fill_rect(self, x, y, w, h, c):
        """Draw a filled rectangle at the given location and size, in the given color."""
        _fill_rect(self, x, y, w, h, c)

    def pixel(self, x, y, c=None):
        """
        Get or set the color of a given pixel.

        If ``c`` is not given, the color of the pixel is returned (or ``None`` if
        ``x, y`` is out of bounds). If ``c`` is given, the pixel is set and
        ``None`` is returned (a no-op if ``x, y`` is out of bounds).
        """
        if x < 0 or x >= self._width or y < 0 or y >= self._height:
            return None
        if c is None:
            return self._format.get_pixel(self, x, y)
        self._format.set_pixel(self, x, y, c)
        return None

    def hline(self, x, y, w, c):
        """Draw a single pixel wide horizontal line."""
        _fill_rect(self, x, y, w, 1, c)

    def vline(self, x, y, h, c):
        """Draw a single pixel wide vertical line."""
        _fill_rect(self, x, y, 1, h, c)

    def rect(self, x, y, w, h, c, f=False):
        """Draw a rectangle at the given location, size and color. ``f`` fills it."""
        if f:
            _fill_rect(self, x, y, w, h, c)
        else:
            _fill_rect(self, x, y, w, 1, c)
            _fill_rect(self, x, y + h - 1, w, 1, c)
            _fill_rect(self, x, y, 1, h, c)
            _fill_rect(self, x + w - 1, y, 1, h, c)

    def line(self, x1, y1, x2, y2, c):
        """Draw a single pixel wide line from (x1, y1) to (x2, y2)."""
        _line(self, x1, y1, x2, y2, c)

    def ellipse(self, x, y, xr, yr, c, f=False, m=_ELLIPSE_MASK_ALL):
        """
        Draw an ellipse centered at (x, y) with radii xr, yr. ``f`` fills it.

        ``m`` is a 4-bit quadrant mask (bit 0 = Q1 top-right, bit 1 = Q2
        top-left, bit 2 = Q3 bottom-left, bit 3 = Q4 bottom-right).
        """
        _ellipse(self, x, y, xr, yr, c, f, m)

    def poly(self, x, y, coords, c, f=False):
        """
        Draw a closed polygon at (x, y) using an array/list of coordinate pairs.

        ``coords`` may be an ``array('h', [x0, y0, x1, y1, ...])`` (as documented
        for MicroPython) or a flat list/tuple of ints, or a list of (x, y) pairs.
        ``f`` fills the polygon; otherwise only the outline is drawn.
        """
        _poly(self, x, y, coords, c, f)

    def scroll(self, xstep, ystep):
        """Shift the contents of the FrameBuffer by (xstep, ystep) pixels."""
        _scroll(self, xstep, ystep)

    def blit(self, source, x, y, key=-1, palette=None):
        """Draw another FrameBuffer (or readonly tuple/list) on top of this one at (x, y)."""
        _blit(self, source, x, y, key, palette)

    def text(self, s, x, y, c=1):
        """
        Write text to the FrameBuffer using (x, y) as the upper-left corner.

        All characters are 8x8 pixels; there is no way to change the font.
        """
        _text(self, s, x, y, c)


def FrameBuffer1(buffer, width, height, format, stride=None):
    """Create a new FrameBuffer object. Here only for historical reasons."""
    return FrameBuffer(buffer, width, height, format, stride)
