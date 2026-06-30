# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Clip-region wrapper for draw targets."""

from ._area import Area
from ._blit_hooks import blit_rect_dispatch

_RGB565_BPP = 2


def intersect_rect(x, y, w, h, clip):
    """Intersect a rectangle with a clip ``Area``. Returns ``Area`` or ``None``."""
    if w <= 0 or h <= 0:
        return None
    hit = Area(x, y, w, h).clip(clip)
    if hit.w <= 0 or hit.h <= 0:
        return None
    return hit


def crop_rgb565_buffer(buf, src_w, src_x, src_y, crop_w, crop_h):
    """Extract a sub-rectangle from a top-down RGB565 buffer."""
    row_bytes = crop_w * _RGB565_BPP
    out = bytearray(row_bytes * crop_h)
    for row in range(crop_h):
        src_start = ((src_y + row) * src_w + src_x) * _RGB565_BPP
        dst_start = row * row_bytes
        out[dst_start : dst_start + row_bytes] = buf[src_start : src_start + row_bytes]
    return out


class ClippedCanvas:
    """Proxy that restricts drawing on ``canvas`` to ``clip``."""

    def __init__(self, canvas, clip):
        self._canvas = canvas
        self._clip = clip
        self._graphics_clip = clip

    def __getattr__(self, name):
        return getattr(self._canvas, name)

    @property
    def width(self):
        return self._canvas.width

    @property
    def height(self):
        return self._canvas.height

    def pixel(self, x, y, c=None):
        if not self._clip.contains(x, y):
            return None
        if c is None:
            return self._canvas.pixel(x, y)
        self._canvas.pixel(x, y, c)
        return Area(x, y, 1, 1)

    def fill(self, c):
        return self.fill_rect(self._clip.x, self._clip.y, self._clip.w, self._clip.h, c)

    def fill_rect(self, x, y, w, h, c):
        hit = intersect_rect(x, y, w, h, self._clip)
        if hit is None:
            return None
        if hasattr(self._canvas, "fill_rect"):
            self._canvas.fill_rect(hit.x, hit.y, hit.w, hit.h, c)
        else:
            for row in range(hit.y, hit.y + hit.h):
                for col in range(hit.x, hit.x + hit.w):
                    self._canvas.pixel(col, row, c)
        return hit

    def hline(self, x, y, w, c):
        return self.fill_rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        return self.fill_rect(x, y, 1, h, c)

    def blit_rect(self, buf, x, y, w, h):
        hit = intersect_rect(x, y, w, h, self._clip)
        if hit is None:
            return None
        dx = hit.x - x
        dy = hit.y - y
        if dx or dy or hit.w != w or hit.h != h:
            buf = crop_rgb565_buffer(buf, w, dx, dy, hit.w, hit.h)
        blit_rect_dispatch(self._canvas, buf, hit.x, hit.y, hit.w, hit.h)
        return hit

    def blit_transparent(self, buf, x, y, w, h, key):
        from ._shapes import blit_transparent

        hit = intersect_rect(x, y, w, h, self._clip)
        if hit is None:
            return None
        dx = hit.x - x
        dy = hit.y - y
        if dx or dy or hit.w != w or hit.h != h:
            buf = crop_rgb565_buffer(buf, w, dx, dy, hit.w, hit.h)
        return blit_transparent(self._canvas, buf, hit.x, hit.y, hit.w, hit.h, key)


class ClipContext:
    """Context manager that pushes a clip rectangle onto a :class:`Draw` stack."""

    def __init__(self, draw, area):
        self._draw = draw
        self._area = area

    def __enter__(self):
        self._draw._clip_stack.append(self._area)
        return self._draw._effective_clip()

    def __exit__(self, exc_type, exc, tb):
        self._clip_stack_pop()

    def _clip_stack_pop(self):
        self._draw._clip_stack.pop()
