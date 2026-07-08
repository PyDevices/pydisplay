# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.boarddisplay — CircuitPython ``board.DISPLAY`` adapter.

Wraps the firmware-preinitialized display with pydisplay's RAM-buffer drawing
API.  On ``show()``, buffer contents are pushed to a displayio ``TileGrid`` and
assigned to ``board.DISPLAY.root_group``.
"""

from displaysys import DisplayDriver, alloc_buffer


class BoardDisplay(DisplayDriver):
    """
    ``DisplayDriver`` for CircuitPython boards with a built-in ``board.DISPLAY``.

    Args:
        display: Optional display object (defaults to ``board.DISPLAY``).
        width (int, optional): Override panel width.
        height (int, optional): Override panel height.
        color_depth (int, optional): Bits per pixel (default 16 / RGB565).
        bitmap_colors (int, optional): ``displayio.Bitmap`` color count (default 65535).
    """

    def __init__(self, display=None, width=None, height=None, color_depth=16, bitmap_colors=65535):
        try:
            import board
        except ImportError as exc:
            raise ImportError("BoardDisplay requires CircuitPython") from exc

        self._display = display if display is not None else board.DISPLAY
        self._width = width if width is not None else self._display.width
        self._height = height if height is not None else self._display.height
        self.color_depth = color_depth
        self._bitmap_colors = bitmap_colors
        self._rotation = getattr(self._display, "rotation", 0) * 90
        self._requires_byteswap = False
        bpp = max(1, color_depth // 8)
        buf = alloc_buffer(self._width * self._height * bpp)
        self._raw_buffer = buf
        self._buffer = memoryview(buf)
        self._group = None
        self._bitmap = None
        self._tile = None
        super().__init__()

    def init(self) -> None:
        pass

    def fill_rect(self, x, y, w, h, c):
        bpp = max(1, self.color_depth // 8)
        mask = (1 << self.color_depth) - 1
        color_bytes = (c & mask).to_bytes(bpp, "little")
        for _y in range(y, y + h):
            begin = (_y * self.width + x) * bpp
            end = begin + w * bpp
            self._buffer[begin:end] = color_bytes * w
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        bpp = max(1, self.color_depth // 8)
        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            raise ValueError("The provided x, y, w, h values are out of range")
        if len(buf) != w * h * bpp:
            raise ValueError("The source buffer is not the correct size")
        for row in range(h):
            source_begin = row * w * bpp
            source_end = source_begin + w * bpp
            dest_begin = ((y + row) * self.width + x) * bpp
            dest_end = dest_begin + w * bpp
            self._buffer[dest_begin:dest_end] = buf[source_begin:source_end]
        return (x, y, w, h)

    def pixel(self, x, y, c):
        return self.fill_rect(x, y, 1, 1, c)

    def _ensure_group(self):
        if self._group is not None:
            return
        import displayio

        colors = self._bitmap_colors
        try:
            bitmap = displayio.Bitmap(self.width, self.height, colors)
        except (ValueError, TypeError):
            colors = 256
            bitmap = displayio.Bitmap(self.width, self.height, colors)
        palette = displayio.Palette(colors)
        if colors > 256:
            for i in range(colors):
                r = ((i >> 11) & 0x1F) * 255 // 31
                g = ((i >> 5) & 0x3F) * 255 // 63
                b = (i & 0x1F) * 255 // 31
                palette[i] = (r << 16) | (g << 8) | b
        else:
            palette[0] = 0x000000
            palette[1] = 0xFFFFFF
        tile = displayio.TileGrid(bitmap, pixel_shader=palette)
        group = displayio.Group()
        group.append(tile)
        self._bitmap = bitmap
        self._tile = tile
        self._group = group

    def _push_buffer(self):
        self._ensure_group()
        bitmap = self._bitmap
        bpp = max(1, self.color_depth // 8)
        if bpp == 2:
            buf = self._buffer
            width = self.width
            for y in range(self.height):
                row = y * width * 2
                for x in range(width):
                    idx = row + x * 2
                    bitmap[x, y] = buf[idx] | (buf[idx + 1] << 8)
            return
        for y in range(self.height):
            for x in range(self.width):
                idx = (y * self.width + x) * bpp
                value = 0
                for i in range(bpp):
                    value |= self._buffer[idx + i] << (8 * i)
                bitmap[x, y] = value

    def show(self, _timer=None) -> None:
        self._push_buffer()
        self._display.root_group = self._group
        refresh = getattr(self._display, "refresh", None)
        if refresh is not None:
            refresh()
