# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.epaperdisplay — E-paper / E-ink displays (work in progress).

CircuitPython board configs may use Adafruit ``EPaperDisplay`` chip drivers
directly until this backend is complete.  The wrapper below provides a
``DisplayDriver`` starting point for MicroPython parity work.
"""

from displaysys import DisplayDriver, alloc_buffer


class EPaperDisplay(DisplayDriver):
    """
    Thin ``DisplayDriver`` wrapper around a CircuitPython ``EPaperDisplay`` chip
    driver or compatible object.

    Drawing is delegated to an internal RAM buffer when present; ``show()``
    triggers a full panel refresh on the underlying driver.

    Args:
        epaper: Chip driver instance (subclass of CircuitPython EPaperDisplay).
        width (int, optional): Panel width in pixels.
        height (int, optional): Panel height in pixels.
        buffer: Optional writable RAM buffer for framebuf operations.
    """

    def __init__(self, epaper, width=None, height=None, buffer=None, color_depth=None):
        self._epaper = epaper
        self._width = width if width is not None else epaper.width
        self._height = height if height is not None else epaper.height
        self.color_depth = color_depth if color_depth is not None else getattr(epaper, "color_depth", 1)
        if buffer is None and self.color_depth <= 8:
            buffer = alloc_buffer(self._width * self._height * max(1, self.color_depth) // 8)
        self._raw_buffer = buffer
        self._buffer = memoryview(buffer) if buffer is not None else None
        self._rotation = 0
        self._requires_byteswap = False
        super().__init__(auto_refresh=False)

    def init(self) -> None:
        pass

    def fill_rect(self, x, y, w, h, c):
        if self._buffer is None:
            raise NotImplementedError(
                "EPaperDisplay wrapper requires a RAM buffer; "
                "use chip driver root_group on CircuitPython for now"
            )
        bpp = max(1, self.color_depth // 8)
        color_bytes = (c & ((1 << self.color_depth) - 1)).to_bytes(bpp, "little")
        for _y in range(y, y + h):
            begin = (_y * self.width + x) * bpp
            end = begin + w * bpp
            self._buffer[begin:end] = color_bytes * w
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        if self._buffer is None:
            raise NotImplementedError("EPaperDisplay wrapper requires a RAM buffer")
        bpp = max(1, self.color_depth // 8)
        for row in range(h):
            source_begin = row * w * bpp
            source_end = source_begin + w * bpp
            dest_begin = ((y + row) * self.width + x) * bpp
            dest_end = dest_begin + w * bpp
            self._buffer[dest_begin:dest_end] = buf[source_begin:source_end]
        return (x, y, w, h)

    def pixel(self, x, y, c):
        return self.fill_rect(x, y, 1, 1, c)

    def show(self, _timer=None) -> None:
        refresh = getattr(self._epaper, "refresh", None)
        if refresh is not None:
            refresh()
            return
        root_group = getattr(self._epaper, "root_group", None)
        if root_group is not None:
            self._epaper.root_group = root_group
