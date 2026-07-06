# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.epaperdisplay — E-paper / E-ink displays.

Wraps CircuitPython ``EPaperDisplay`` chip drivers with a pydisplay RAM
buffer.  On ``show()``, buffer contents are pushed through displayio (CP)
or ``bus.send`` (MP path) before calling ``refresh()``.
"""

from displaysys import DisplayDriver, alloc_buffer


class EPaperDisplay(DisplayDriver):
    """
    ``DisplayDriver`` wrapper around a CircuitPython ``EPaperDisplay`` chip driver.

    Args:
        epaper: Chip driver instance (subclass of CircuitPython EPaperDisplay).
        width (int, optional): Panel width in pixels.
        height (int, optional): Panel height in pixels.
        buffer: Optional writable RAM buffer for framebuf operations.
        color_depth (int, optional): Bits per pixel (default 1 for monochrome).
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
        self._displayio_group = None
        super().__init__(auto_refresh=False)

    def init(self) -> None:
        pass

    def fill_rect(self, x, y, w, h, c):
        if self._buffer is None:
            raise NotImplementedError("EPaperDisplay requires a RAM buffer")
        if self.color_depth == 1:
            on = 1 if (c & 1) else 0
            for _y in range(y, y + h):
                for _x in range(x, x + w):
                    self._set_1bpp_pixel(_x, _y, on)
            return (x, y, w, h)
        bpp = max(1, self.color_depth // 8)
        color_bytes = (c & ((1 << self.color_depth) - 1)).to_bytes(bpp, "little")
        for _y in range(y, y + h):
            begin = (_y * self.width + x) * bpp
            end = begin + w * bpp
            self._buffer[begin:end] = color_bytes * w
        return (x, y, w, h)

    def _set_1bpp_pixel(self, x, y, on):
        idx = y * self.width + x
        byte_i = idx // 8
        bit = 7 - (idx % 8)
        if on:
            self._buffer[byte_i] |= 1 << bit
        else:
            self._buffer[byte_i] &= ~(1 << bit) & 0xFF

    def blit_rect(self, buf, x, y, w, h):
        if self._buffer is None:
            raise NotImplementedError("EPaperDisplay requires a RAM buffer")
        if self.color_depth == 1:
            for row in range(h):
                for col in range(w):
                    src = row * w + col
                    byte_i = src // 8
                    bit = 7 - (src % 8)
                    on = (buf[byte_i] >> bit) & 1
                    self._set_1bpp_pixel(x + col, y + row, on)
            return (x, y, w, h)
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

    def _push_buffer_displayio(self):
        import displayio

        if self._displayio_group is None:
            bitmap = displayio.Bitmap(self.width, self.height, 2)
            palette = displayio.Palette(2)
            palette[0] = 0xFFFFFF
            palette[1] = 0x000000
            tile = displayio.TileGrid(bitmap, pixel_shader=palette)
            group = displayio.Group()
            group.append(tile)
            self._displayio_group = group
            self._displayio_bitmap = bitmap
        bitmap = self._displayio_bitmap
        inverted = getattr(self._epaper, "black_bits_inverted", False)
        for y in range(self.height):
            for x in range(self.width):
                idx = y * self.width + x
                byte_i = idx // 8
                bit = 7 - (idx % 8)
                on = (self._buffer[byte_i] >> bit) & 1
                if inverted:
                    on = 1 - on
                bitmap[x, y] = on
        self._epaper.root_group = self._displayio_group

    def _push_buffer_bus(self):
        ep = self._epaper
        bus = getattr(ep, "bus", None)
        write_cmd = getattr(ep, "write_black_ram_command", None)
        if bus is None or write_cmd is None or self._buffer is None:
            return False
        colstart = getattr(ep, "colstart", 0)
        rowstart = getattr(ep, "rowstart", 0)
        x0 = colstart
        y0 = rowstart
        x1 = x0 + self.width - 1
        y1 = y0 + self.height - 1
        little = getattr(ep, "address_little_endian", False)
        if little:
            win = bytes([x0 & 0xFF, x0 >> 8, x1 & 0xFF, x1 >> 8])
        else:
            win = bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])
        set_col = getattr(ep, "set_column_window_command", None)
        set_row = getattr(ep, "set_row_window_command", None)
        set_cur_col = getattr(ep, "set_current_column_command", None)
        set_cur_row = getattr(ep, "set_current_row_command", None)
        if set_col is not None:
            bus.send(set_col, win)
        if set_row is not None:
            bus.send(set_row, bytes([y0 & 0xFF, y0 >> 8, y1 & 0xFF, y1 >> 8]))
        if set_cur_col is not None:
            bus.send(set_cur_col, win[:2])
        if set_cur_row is not None:
            bus.send(set_cur_row, bytes([y0 & 0xFF, y0 >> 8]))
        data = self._buffer
        if getattr(ep, "black_bits_inverted", False):
            data = bytes(b ^ 0xFF for b in self._buffer)
        bus.send(write_cmd, data)
        return True

    def show(self, _timer=None) -> None:
        if self._buffer is not None:
            try:
                self._push_buffer_displayio()
            except ImportError:
                self._push_buffer_bus()
        refresh = getattr(self._epaper, "refresh", None)
        if refresh is not None:
            refresh()
