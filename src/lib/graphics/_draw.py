# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`graphics._draw`
====================================================
Graphics Draw class
"""

from . import _font, _shapes


class Draw:
    """
    Draw shapes on a canvas (display, FrameBuffer, or compatible object).

    Each method delegates to ``graphics._shapes`` and returns an ``Area`` bounding box.

    Args:
        canvas: Object with framebuf-compatible drawing methods.

    Example:
        ```python
        draw = Draw(display)
        draw.fill(0x0000)
        draw.rect(10, 10, 100, 100, 0xFFFF)
        ```
    """

    def __init__(self, canvas):
        self.canvas = canvas

    def arc(self, x, y, r, a0, a1, c):
        """Draw an arc. Returns Area bounds."""
        return _shapes.arc(self.canvas, x, y, r, a0, a1, c)

    def blit(self, source, x, y, key=-1, palette=None):
        """Blit a source buffer. Returns Area bounds."""
        return _shapes.blit(self.canvas, source, x, y, key, palette)

    def blit_rect(self, buf, x, y, w, h):
        """Blit a raw rectangle buffer. Returns Area bounds."""
        return _shapes.blit_rect(self.canvas, buf, x, y, w, h)

    def blit_transparent(self, buf, x, y, w, h, key=None):
        """Blit with transparency. Returns Area bounds."""
        return _shapes.blit_transparent(self.canvas, buf, x, y, w, h, key)

    def circle(self, x, y, r, c, f=False):
        """Draw a circle. Returns Area bounds."""
        return _shapes.circle(self.canvas, x, y, r, c, f)

    def ellipse(self, x, y, r1, r2, c, f=False, m=0b1111, w=None, h=None):
        """Draw an ellipse. Returns Area bounds."""
        return _shapes.ellipse(self.canvas, x, y, r1, r2, c, f, m, w, h)

    def fill(self, c):
        """Fill the canvas. Returns Area bounds."""
        return _shapes.fill(self.canvas, c)

    def fill_rect(self, x, y, w, h, c):
        """Fill a rectangle. Returns Area bounds."""
        return _shapes.fill_rect(self.canvas, x, y, w, h, c)

    def gradient_rect(self, x, y, w, h, c1, c2=None, vertical=True):
        """Fill a rectangle with a gradient. Returns Area bounds."""
        return _shapes.gradient_rect(self.canvas, x, y, w, h, c1, c2, vertical)

    def hline(self, x, y, w, c):
        """Draw a horizontal line. Returns Area bounds."""
        return _shapes.hline(self.canvas, x, y, w, c)

    def line(self, x1, y1, x2, y2, c):
        """Draw a line. Returns Area bounds."""
        return _shapes.line(self.canvas, x1, y1, x2, y2, c)

    def pixel(self, x, y, c):
        """Draw a pixel. Returns Area bounds."""
        return _shapes.pixel(self.canvas, x, y, c)

    def poly(self, x, y, coords, c, f=False):
        """Draw a polygon from flat coordinates. Returns Area bounds."""
        return _shapes.poly(self.canvas, x, y, coords, c, f)

    def polygon(self, points, x, y, c, angle=0, center_x=0, center_y=0):
        """Draw a polygon from point list. Returns Area bounds."""
        return _shapes.polygon(self.canvas, points, x, y, c, angle, center_x, center_y)

    def rect(self, x, y, w, h, c, f=False):
        """Draw a rectangle. Returns Area bounds."""
        return _shapes.rect(self.canvas, x, y, w, h, c, f)

    def round_rect(self, x, y, w, h, r, c, f=False):
        """Draw a rounded rectangle. Returns Area bounds."""
        return _shapes.round_rect(self.canvas, x, y, w, h, r, c, f)

    def triangle(self, x1, y1, x2, y2, x3, y3, c, f=False):
        """Draw a triangle. Returns Area bounds."""
        return _shapes.triangle(self.canvas, x1, y1, x2, y2, x3, y3, c, f)

    def vline(self, x, y, h, c):
        """Draw a vertical line. Returns Area bounds."""
        return _shapes.vline(self.canvas, x, y, h, c)

    def text(self, *args, **kwargs):
        """Draw text using height from kwargs. Returns Area bounds."""
        return _font.text(self.canvas, *args, **kwargs)

    def text8(self, *args, **kwargs):
        """Draw 8px-high text. Returns Area bounds."""
        return _font.text8(self.canvas, *args, **kwargs)

    def text14(self, *args, **kwargs):
        """Draw 14px-high text. Returns Area bounds."""
        return _font.text14(self.canvas, *args, **kwargs)

    def text16(self, *args, **kwargs):
        """Draw 16px-high text. Returns Area bounds."""
        return _font.text16(self.canvas, *args, **kwargs)
