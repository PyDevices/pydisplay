# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.rgbdisplay — RGB parallel panel framebuffer adapter.

Wraps a panel object from ``pydevices/displayif`` (or compatible) that can
present an RGB565 RAM buffer to the display.  The panel protocol is duck-typed:

- ``present(x, y, width, height, buffer)`` — preferred (displayif)
- ``bitmap(x, y, width, height, buffer)`` — legacy alias during bring-up
"""

from displaysys import DisplayDriver, alloc_buffer


class RGBDisplay(DisplayDriver):
    """
    ``DisplayDriver`` for SoC RGB parallel panels (RGB565).

    Args:
        panel: Object implementing ``present()`` or ``bitmap()``.
        width (int): Panel width in pixels.
        height (int): Panel height in pixels.
        color_depth (int): Bits per pixel (16 for RGB565).
        buffer: Optional pre-allocated draw buffer.
    """

    def __init__(self, panel, width, height, color_depth=16, buffer=None):
        self._panel = panel
        self._width = width
        self._height = height
        self.color_depth = color_depth
        bpp = color_depth // 8
        if buffer is None:
            buffer = alloc_buffer(width * height * bpp)
        self._raw_buffer = buffer
        self._buffer = memoryview(buffer)
        self._rotation = 0
        self._requires_byteswap = False
        super().__init__(auto_refresh=False)

    def init(self) -> None:
        backlight_on = getattr(self._panel, "backlight_on", None)
        if backlight_on is not None:
            backlight_on()

    def fill_rect(self, x, y, w, h, c):
        bpp = self.color_depth // 8
        color_bytes = (c & 0xFFFF).to_bytes(bpp, "little")
        for _y in range(y, y + h):
            begin = (_y * self.width + x) * bpp
            end = begin + w * bpp
            self._buffer[begin:end] = color_bytes * w
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        bpp = self.color_depth // 8
        for row in range(h):
            source_begin = row * w * bpp
            source_end = source_begin + w * bpp
            dest_begin = ((y + row) * self.width + x) * bpp
            dest_end = dest_begin + w * bpp
            self._buffer[dest_begin:dest_end] = buf[source_begin:source_end]
        return (x, y, w, h)

    def pixel(self, x, y, c):
        return self.fill_rect(x, y, 1, 1, c)

    def _present_buffer(self):
        present = getattr(self._panel, "present", None)
        if present is None:
            present = getattr(self._panel, "bitmap", None)
        if present is None:
            raise NotImplementedError(
                "RGB panel must implement present(x, y, w, h, buffer) or bitmap(...)"
            )
        present(0, 0, self.width, self.height, self._buffer)

    def show(self, _timer=None) -> None:
        self._present_buffer()

    def deinit(self) -> None:
        backlight_off = getattr(self._panel, "backlight_off", None)
        if backlight_off is not None:
            backlight_off()
        deinit = getattr(self._panel, "deinit", None)
        if deinit is not None:
            deinit()
