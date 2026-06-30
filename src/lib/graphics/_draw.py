# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`graphics._draw`
====================================================
Graphics Draw class
"""

from . import _font, _shapes
from ._area import Area
from ._clip import ClipContext, ClippedCanvas


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

        with draw.clip(5, 5, 50, 30):
            draw.fill_rect(0, 0, 200, 200, 0xF800)  # clipped to the 50x30 region
        ```
    """

    def __init__(self, canvas):
        self.canvas = canvas
        self._clip_stack = []

    def clip(self, x, y=None, w=None, h=None):
        """Return a context manager that clips drawing to a rectangle.

        Accepts ``clip(x, y, w, h)`` or ``clip(Area(...))``. Nested clips intersect.
        """
        if isinstance(x, Area):
            area = x
        elif y is None or w is None or h is None:
            raise ValueError("clip() requires x, y, w, h or an Area")
        else:
            area = Area(x, y, w, h)
        return ClipContext(self, area)

    def _effective_clip(self):
        if not self._clip_stack:
            return None
        clip = self._clip_stack[0]
        for extra in self._clip_stack[1:]:
            clip = clip.clip(extra)
        bounds = Area(0, 0, self.canvas.width, self.canvas.height)
        clip = clip.clip(bounds)
        if clip.w <= 0 or clip.h <= 0:
            return Area(0, 0, 0, 0)
        return clip

    def _target(self):
        clip = self._effective_clip()
        if clip is None:
            return self.canvas
        return ClippedCanvas(self.canvas, clip)

    def arc(self, x, y, r, a0, a1, c):
        """Draw an arc. Returns Area bounds."""
        return _shapes.arc(self._target(), x, y, r, a0, a1, c)

    def blit(self, source, x, y, key=-1, palette=None):
        """Blit a source buffer. Returns Area bounds."""
        return _shapes.blit(self._target(), source, x, y, key, palette)

    def blit_rect(self, buf, x, y, w, h):
        """Blit a raw rectangle buffer. Returns Area bounds."""
        return _shapes.blit_rect(self._target(), buf, x, y, w, h)

    def blit_transparent(self, buf, x, y, w, h, key=None):
        """Blit with transparency. Returns Area bounds."""
        return _shapes.blit_transparent(self._target(), buf, x, y, w, h, key)

    def circle(self, x, y, r, c, f=False):
        """Draw a circle. Returns Area bounds."""
        return _shapes.circle(self._target(), x, y, r, c, f)

    def ellipse(self, x, y, r1, r2, c, f=False, m=0b1111, w=None, h=None):
        """Draw an ellipse. Returns Area bounds."""
        return _shapes.ellipse(self._target(), x, y, r1, r2, c, f, m, w, h)

    def fill(self, c):
        """Fill the canvas. Returns Area bounds."""
        return _shapes.fill(self._target(), c)

    def fill_rect(self, x, y, w, h, c):
        """Fill a rectangle. Returns Area bounds."""
        return _shapes.fill_rect(self._target(), x, y, w, h, c)

    def gradient_rect(self, x, y, w, h, c1, c2=None, vertical=True):
        """Fill a rectangle with a gradient. Returns Area bounds."""
        return _shapes.gradient_rect(self._target(), x, y, w, h, c1, c2, vertical)

    def hline(self, x, y, w, c):
        """Draw a horizontal line. Returns Area bounds."""
        return _shapes.hline(self._target(), x, y, w, c)

    def line(self, x1, y1, x2, y2, c):
        """Draw a line. Returns Area bounds."""
        return _shapes.line(self._target(), x1, y1, x2, y2, c)

    def pixel(self, x, y, c):
        """Draw a pixel. Returns Area bounds."""
        return _shapes.pixel(self._target(), x, y, c)

    def poly(self, x, y, coords, c, f=False):
        """Draw a polygon from flat coordinates. Returns Area bounds."""
        return _shapes.poly(self._target(), x, y, coords, c, f)

    def polygon(self, points, x, y, c, angle=0, center_x=0, center_y=0):
        """Draw a polygon from point list. Returns Area bounds."""
        return _shapes.polygon(self._target(), points, x, y, c, angle, center_x, center_y)

    def rect(self, x, y, w, h, c, f=False):
        """Draw a rectangle. Returns Area bounds."""
        return _shapes.rect(self._target(), x, y, w, h, c, f)

    def round_rect(self, x, y, w, h, r, c, f=False):
        """Draw a rounded rectangle. Returns Area bounds."""
        return _shapes.round_rect(self._target(), x, y, w, h, r, c, f)

    def triangle(self, x1, y1, x2, y2, x3, y3, c, f=False):
        """Draw a triangle. Returns Area bounds."""
        return _shapes.triangle(self._target(), x1, y1, x2, y2, x3, y3, c, f)

    def vline(self, x, y, h, c):
        """Draw a vertical line. Returns Area bounds."""
        return _shapes.vline(self._target(), x, y, h, c)

    def text(self, *args, **kwargs):
        """Draw text using height from kwargs. Returns Area bounds."""
        return _font.text(self._target(), *args, **kwargs)

    def text8(self, *args, **kwargs):
        """Draw 8px-high text. Returns Area bounds."""
        return _font.text8(self._target(), *args, **kwargs)

    def text14(self, *args, **kwargs):
        """Draw 14px-high text. Returns Area bounds."""
        return _font.text14(self._target(), *args, **kwargs)

    def text16(self, *args, **kwargs):
        """Draw 16px-high text. Returns Area bounds."""
        return _font.text16(self._target(), *args, **kwargs)
