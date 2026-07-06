# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.dpidisplay — ESP32 RGB/DPI panel wrapper.

Wraps LilyGO ``lcd.DPI`` (or compatible) framebuffers for pydisplay drawing.
"""

from displaysys import DisplayDriver, alloc_buffer


class DPIDisplay(DisplayDriver):
    """
    DisplayDriver for ESP32-S3 RGB DPI panels after chip init.

    Args:
        panel: Object with ``bitmap(x, y, w, h, data)`` and optional ``backlight_on/off``.
        width (int): Panel width in pixels.
        height (int): Panel height in pixels.
        color_depth (int): Bits per pixel (16 for RGB565).
        buffer: Optional pre-allocated RGB565 buffer.
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
        backlight = getattr(self._panel, "backlight_on", None)
        if backlight is not None:
            backlight()

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

    def show(self, _timer=None) -> None:
        self._panel.bitmap(0, 0, self.width, self.height, self._buffer)

    def deinit(self) -> None:
        backlight = getattr(self._panel, "backlight_off", None)
        if backlight is not None:
            backlight()
        deinit = getattr(self._panel, "deinit", None)
        if deinit is not None:
            deinit()
