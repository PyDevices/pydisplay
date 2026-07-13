# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from graphics import RGB565, FrameBuffer

from ._constants import DEFAULT_PADDING
from .widget import Widget


class Icon(Widget):
    cache = {}
    # Reusable 2-entry (bg, fg) palette. Rewritten on every draw, so a single
    # shared buffer avoids allocating a 4-byte FrameBuffer per draw call.
    _palette = FrameBuffer(memoryview(bytearray(4)), 2, 1, RGB565)

    def __init__(
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
        Initialize an Icon widget to display an icon.

        Two asset kinds are supported, both loaded via ``FrameBuffer.from_file``:

        * **Monochrome ``.pbm``** (1 bit-per-pixel) — recolored to the icon's
          ``fg``/``bg`` at draw time via a 2-entry palette (the default).
        * **Color RGB565 ``.bmp`` (BMP565)** — blitted as-is; pass ``chroma`` to
          treat one color as transparent. No PNG is used anywhere.

        Args:
            parent (Widget): The parent widget or screen that contains this icon.
            x (int): The x-coordinate of the icon.
            y (int): The y-coordinate of the icon.
            w (int): The width of the icon.
            h (int): The height of the icon.
            align (int): The alignment of the icon.
            align_to (Widget): The widget to align to.
            fg (int): The color of the icon (monochrome assets only).
            bg (int): The background color of the icon.
            visible (bool): The visibility of the icon.
            value (str): The icon file to display (``.pbm`` or BMP565 ``.bmp``).
            padding (tuple): The padding on each side of the icon.
            chroma (int): Transparent color key for color (BMP565) icons.

        Usage:
            icon = Icon(screen, value="icon.pbm")
            status = Icon(bar, value="battery_color_24dp.bmp")
        """
        if not value:
            raise ValueError("Icon value must be set to the filename with path.")
        self.chroma = chroma
        self.load_icon(value)
        padding = padding if padding is not None else DEFAULT_PADDING
        w = w or self._icon_width + padding[0] + padding[2]
        h = h or self._icon_height + padding[1] + padding[3]
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def load_icon(self, value):
        """Load icon file, cache it, and record whether it is a color asset."""
        if value in Icon.cache:
            self._fbuf = Icon.cache[value]
        else:
            self._fbuf = FrameBuffer.from_file(value)
            Icon.cache[value] = self._fbuf
        self._icon_width, self._icon_height = self._fbuf.width, self._fbuf.height
        self._is_color = self._fbuf.format == RGB565
        self._swapped = None

    def _swapped_color(self):
        """Return (byteswapped color FrameBuffer, swapped chroma), cached."""
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

    def changed(self):
        """Update the icon when the value (file) changes."""
        self.display.framebuf.fill_rect(*self.padded_area, self.bg)
        self.load_icon(self.value)
        super().changed()

    def draw(self, _=None):
        """
        Draw the icon on the screen.

        Color (BMP565) icons are blitted directly (with ``chroma`` as the
        transparent key when set); monochrome icons are recolored to
        ``fg``/``bg`` via the shared 2-entry palette buffer.
        """
        px, py = self.padded_area.x, self.padded_area.y
        if self._is_color:
            fbuf = self._fbuf
            chroma = self.chroma
            # BMP565 assets are stored non-swapped; match the display's byte
            # order when it draws pre-swapped colors (swapped MCU panels).
            if self.display.needs_swap:
                fbuf, chroma = self._swapped_color()
            if chroma is not None:
                self.display.framebuf.blit(fbuf, px, py, chroma)
            else:
                self.display.framebuf.blit(fbuf, px, py)
            return
        pal = Icon._palette
        if self.bg is self.parent.color_theme.transparent:
            key = ~self.fg
            pal.pixel(0, 0, key)
        else:
            key = -1
            pal.pixel(0, 0, self.bg)
        pal.pixel(1, 0, self.fg)
        self.display.framebuf.blit(self._fbuf, px, py, key, pal)
