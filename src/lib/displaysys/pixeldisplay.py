# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.pixeldisplay — addressable LED grids (NeoPixel, DotStar, etc.).

Wraps a software pixel framebuffer that flushes with ``show()`` rather than
``refresh()``.  On CircuitPython this is typically ``adafruit_pixel_framebuf``.
"""

from displaysys import DisplayDriver


class PixelDisplay(DisplayDriver):
    """
    DisplayDriver for addressable-LED matrix layouts.

    Args:
        pixel_buffer: Object with framebuf drawing API and ``show()`` (e.g.
            ``PixelFramebuffer``).
        width (int, optional): Override width; defaults to ``pixel_buffer.width``.
        height (int, optional): Override height; defaults to ``pixel_buffer.height``.
        color_depth (int, optional): Bits per pixel. Defaults to 24 (RGB888).
    """

    def __init__(self, pixel_buffer, width=None, height=None, color_depth=24):
        self._raw_buffer = pixel_buffer
        self._width = width if width is not None else pixel_buffer.width
        self._height = height if height is not None else pixel_buffer.height
        self._rotation = 0
        self.color_depth = color_depth
        self._requires_byteswap = False
        super().__init__(auto_refresh=False)

    def init(self) -> None:
        pass

    def _draw(self, method, *args):
        fn = getattr(self._raw_buffer, method, None)
        if fn is None:
            raise AttributeError(f"pixel buffer has no {method!r}")
        return fn(*args)

    def fill_rect(self, x, y, w, h, c):
        return self._draw("fill_rect", x, y, w, h, c)

    def blit_rect(self, buf, x, y, w, h):
        fn = getattr(self._raw_buffer, "blit", None)
        if fn is not None:
            return fn(buf, x, y, w, h)
        # Fallback: per-row blit via fill_rect if buffer is raw bytes
        bpp = max(1, self.color_depth // 8)
        row_bytes = w * bpp
        for row in range(h):
            row_buf = buf[row * row_bytes : (row + 1) * row_bytes]
            self._draw("blit", row_buf, x, y + row, w, 1)
        return (x, y, w, h)

    def pixel(self, x, y, c):
        return self._draw("pixel", x, y, c)

    def show(self, _timer=None) -> None:
        self._raw_buffer.show()
