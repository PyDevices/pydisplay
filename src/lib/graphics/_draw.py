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
    A Draw class to draw shapes onto a specified canvas.

    Args:
        canvas (Canvas): The canvas to draw on.

    Usage:
    ```
    # canvas is an instance of DisplayDriver, FrameBuffer, or other canvas-like object
    draw = Draw(canvas)
    draw.fill(0x0000)
    draw.rect(10, 10, 100, 100, 0xFFFF)
    ```
    """

    def __init__(self, canvas):
        self.canvas = canvas

    def arc(self, x, y, r, a0, a1, c):
        return _shapes.arc(self.canvas, x, y, r, a0, a1, c)

    def blit(self, source, x, y, key=-1, palette=None):
        return _shapes.blit(self.canvas, source, x, y, key, palette)

    def blit_rect(self, buf, x, y, w, h):
        return _shapes.blit_rect(self.canvas, buf, x, y, w, h)

    def blit_tranparent(self, buf, x, y, w, h, key=None):
        return _shapes.blit_transparent(self.canvas, buf, x, y, w, h, key)

    def circle(self, x, y, r, c, f=False):
        return _shapes.circle(self.canvas, x, y, r, c, f)

    def ellipse(self, x, y, r1, r2, c, f=False, m=0b1111, w=None, h=None):
        return _shapes.ellipse(self.canvas, x, y, r1, r2, c, f, m, w, h)

    def fill(self, c):
        return _shapes.fill(self.canvas, c)

    def fill_rect(self, x, y, w, h, c):
        return _shapes.fill_rect(self.canvas, x, y, w, h, c)

    def gradient_rect(self, x, y, w, h, c1, c2=None, vertical=True):
        return _shapes.gradient_rect(self.canvas, x, y, w, h, c1, c2, vertical)

    def hline(self, x, y, w, c):
        return _shapes.hline(self.canvas, x, y, w, c)

    def line(self, x1, y1, x2, y2, c):
        return _shapes.line(self.canvas, x1, y1, x2, y2, c)

    def pixel(self, x, y, c):
        return _shapes.pixel(self.canvas, x, y, c)

    def poly(self, x, y, coords, c, f=False):
        return _shapes.poly(self.canvas, x, y, coords, c, f)

    def polygon(self, points, x, y, c, angle=0, center_x=0, center_y=0):
        return _shapes.polygon(self.canvas, points, x, y, c, angle, center_x, center_y)

    def rect(self, x, y, w, h, c, f=False):
        return _shapes.rect(self.canvas, x, y, w, h, c, f)

    def round_rect(self, x, y, w, h, r, c, f=False):
        return _shapes.round_rect(self.canvas, x, y, w, h, r, c, f)

    def triangle(self, x1, y1, x2, y2, x3, y3, c, f=False):
        return _shapes.triangle(self.canvas, x1, y1, x2, y2, x3, y3, c, f)

    def vline(self, x, y, h, c):
        return _shapes.vline(self.canvas, x, y, h, c)

    def text(self, *args, **kwargs):
        return _font.text(self.canvas, *args, **kwargs)

    def text8(self, *args, **kwargs):
        return _font.text8(self.canvas, *args, **kwargs)

    def text14(self, *args, **kwargs):
        return _font.text14(self.canvas, *args, **kwargs)

    def text16(self, *args, **kwargs):
        return _font.text16(self.canvas, *args, **kwargs)
