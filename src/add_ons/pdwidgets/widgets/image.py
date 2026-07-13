# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from graphics import RGB565, FrameBuffer

from .._constants import DEFAULT_PADDING
from ..widget import Widget


class Image(Widget):
    cache = {}

    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
        chroma=None,
    ):
        """
        Raster image widget (``.pbm`` or BMP565 ``.bmp``), same loaders as Icon.

        Use for logos / gallery frames that are not tiny monochrome icons.
        When ``value`` is ``None``, a solid ``bg`` placeholder rect is drawn.
        """
        self.chroma = chroma
        self._fbuf = None
        self._is_color = False
        self._swapped = None
        if value:
            self._load(value)
            padding = padding if padding is not None else DEFAULT_PADDING
            w = w or self._img_w + padding[0] + padding[2]
            h = h or self._img_h + padding[1] + padding[3]
        else:
            w = w or parent.width // 2
            h = h or parent.height // 3
            padding = padding if padding is not None else DEFAULT_PADDING
        bg = bg if bg is not None else parent.color_theme.surface_variant
        fg = fg if fg is not None else parent.color_theme.on_surface
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def _load(self, value):
        if value in Image.cache:
            self._fbuf = Image.cache[value]
        else:
            self._fbuf = FrameBuffer.from_file(value)
            Image.cache[value] = self._fbuf
        self._img_w, self._img_h = self._fbuf.width, self._fbuf.height
        self._is_color = self._fbuf.format == RGB565
        self._swapped = None

    def changed(self):
        if self._value:
            self._load(self._value)
        else:
            self._fbuf = None
        super().changed()

    def _swapped_color(self):
        if self._swapped is None:
            src = self._fbuf.buffer
            swp = bytearray(len(src))
            swp[0::2] = src[1::2]
            swp[1::2] = src[0::2]
            fbuf = FrameBuffer(memoryview(swp), self._fbuf.width, self._fbuf.height, RGB565)
            chroma = self.chroma
            if chroma is not None:
                chroma = ((chroma & 0xFF) << 8) | (chroma >> 8)
            self._swapped = (fbuf, chroma)
        return self._swapped

    def draw(self, _=None):
        """Blit the image or a placeholder rectangle."""
        self.parent.draw(self.area)
        pa = self.padded_area
        if self._fbuf is None:
            self.display.framebuf.fill_rect(*pa, self.bg)
            # Simple diagonal to look like a "picture" placeholder.
            self.display.framebuf.line(pa.x, pa.y, pa.x + pa.w - 1, pa.y + pa.h - 1, self.fg)
            self.display.framebuf.line(pa.x + pa.w - 1, pa.y, pa.x, pa.y + pa.h - 1, self.fg)
            self.display.framebuf.rect(pa.x, pa.y, pa.w, pa.h, self.fg)
            return
        px, py = pa.x, pa.y
        if self._is_color:
            fbuf = self._fbuf
            chroma = self.chroma
            if self.display.needs_swap:
                fbuf, chroma = self._swapped_color()
            if chroma is not None:
                self.display.framebuf.blit(fbuf, px, py, chroma)
            else:
                self.display.framebuf.blit(fbuf, px, py)
            return
        # Monochrome: recolor like Icon
        from graphics import RGB565 as _RGB  # local; palette buffer

        pal = FrameBuffer(memoryview(bytearray(4)), 2, 1, _RGB)
        key = -1
        pal.pixel(0, 0, self.bg)
        pal.pixel(1, 0, self.fg)
        self.display.framebuf.blit(self._fbuf, px, py, key, pal)
