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

# ACeP 7-color palette indices (matches Adafruit acep7in driver conventions).
_ACEP_PALETTE_RGB = (
    0x000000,
    0xFFFFFF,
    0x00FF00,
    0x0000FF,
    0xFF0000,
    0xFFFF00,
    0xFFA500,
)


class EPaperDisplay(DisplayDriver):
    """
    ``DisplayDriver`` wrapper around a CircuitPython ``EPaperDisplay`` chip driver.

    Packed buffer depths:
    - ``color_depth=1`` — monochrome (1 bit per pixel)
    - ``color_depth=2`` — tri-color or 4-gray (2 bits per pixel: 0=white, 1=black, 2=accent)
    - ``color_depth=4`` — ACeP / advanced color (4 bits per pixel, 2 per byte)
    """

    def __init__(
        self, epaper, width=None, height=None, buffer=None, color_depth=None, *, quiet=False
    ):
        self._epaper = epaper
        self._width = width if width is not None else epaper.width
        self._height = height if height is not None else epaper.height
        self.color_depth = (
            color_depth if color_depth is not None else getattr(epaper, "color_depth", 1)
        )
        if buffer is None and self.color_depth <= 8:
            buffer = alloc_buffer(self._buffer_byte_size())
        self._raw_buffer = buffer
        self._buffer = memoryview(buffer) if buffer is not None else None
        self._rotation = 0
        self._requires_byteswap = False
        self._displayio_group = None
        super().__init__(quiet=quiet)

    def _buffer_byte_size(self):
        return (self._width * self._height * self.color_depth + 7) // 8

    def _pixel_index(self, x, y):
        return y * self.width + x

    def _set_packed_pixel(self, x, y, value):
        idx = self._pixel_index(x, y)
        if self.color_depth == 1:
            byte_i = idx // 8
            bit = 7 - (idx % 8)
            if value & 1:
                self._buffer[byte_i] |= 1 << bit
            else:
                self._buffer[byte_i] &= ~(1 << bit) & 0xFF
            return
        if self.color_depth == 2:
            shift = 6 - (idx % 4) * 2
            byte_i = idx // 4
            self._buffer[byte_i] = (self._buffer[byte_i] & ~(0x03 << shift)) | (
                (value & 0x03) << shift
            )
            return
        if self.color_depth == 4:
            shift = 4 if idx & 1 else 0
            byte_i = idx // 2
            self._buffer[byte_i] = (self._buffer[byte_i] & ~(0x0F << shift)) | (
                (value & 0x0F) << shift
            )
            return
        bpp = self.color_depth // 8
        begin = idx * bpp
        color_bytes = (value & ((1 << self.color_depth) - 1)).to_bytes(bpp, "little")
        self._buffer[begin : begin + bpp] = color_bytes

    def _get_packed_pixel(self, x, y):
        idx = self._pixel_index(x, y)
        if self.color_depth == 1:
            byte_i = idx // 8
            bit = 7 - (idx % 8)
            return (self._buffer[byte_i] >> bit) & 1
        if self.color_depth == 2:
            shift = 6 - (idx % 4) * 2
            return (self._buffer[idx // 4] >> shift) & 0x03
        if self.color_depth == 4:
            shift = 4 if idx & 1 else 0
            return (self._buffer[idx // 2] >> shift) & 0x0F
        bpp = self.color_depth // 8
        begin = idx * bpp
        return int.from_bytes(self._buffer[begin : begin + bpp], "little")

    def init(self) -> None:
        pass

    def fill_rect(self, x, y, w, h, c):
        if self._buffer is None:
            raise NotImplementedError("EPaperDisplay requires a RAM buffer")
        if self.color_depth <= 4:
            mask = (1 << self.color_depth) - 1
            value = c & mask
            for _y in range(y, y + h):
                for _x in range(x, x + w):
                    self._set_packed_pixel(_x, _y, value)
            return (x, y, w, h)
        bpp = self.color_depth // 8
        color_bytes = (c & ((1 << self.color_depth) - 1)).to_bytes(bpp, "little")
        for _y in range(y, y + h):
            begin = (_y * self.width + x) * bpp
            end = begin + w * bpp
            self._buffer[begin:end] = color_bytes * w
        return (x, y, w, h)

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
                    self._set_packed_pixel(x + col, y + row, on)
            return (x, y, w, h)
        if self.color_depth in (2, 4):
            pixels_per_byte = 8 // self.color_depth
            mask = (1 << self.color_depth) - 1
            for row in range(h):
                for col in range(w):
                    src = row * w + col
                    shift = (8 - self.color_depth) - (src % pixels_per_byte) * self.color_depth
                    value = (buf[src // pixels_per_byte] >> shift) & mask
                    self._set_packed_pixel(x + col, y + row, value)
            return (x, y, w, h)
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

    def _panel_buffer(self):
        """Return buffer bytes in panel-native packing (may alias ``_buffer``)."""
        if self.color_depth in (1, 2, 4):
            return bytes(self._buffer)
        return self._buffer

    def _tri_color_planes(self):
        """Split 2bpp buffer into black and highlight 1bpp planes."""
        size = (self.width * self.height + 7) // 8
        black = bytearray(size)
        color = bytearray(size)
        for y in range(self.height):
            for x in range(self.width):
                value = self._get_packed_pixel(x, y)
                idx = self._pixel_index(x, y)
                bit = 7 - (idx % 8)
                byte_i = idx // 8
                if value == 1:
                    black[byte_i] |= 1 << bit
                elif value == 2:
                    color[byte_i] |= 1 << bit
        return black, color

    def _send_ram_window(self, ep, bus):
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

    def _push_buffer_displayio(self):
        import displayio

        if self.color_depth == 1:
            colors = 2
        elif self.color_depth == 4:
            colors = 16
        else:
            colors = 4

        if self._displayio_group is None:
            bitmap = displayio.Bitmap(self.width, self.height, colors)
            palette = displayio.Palette(colors)
            if self.color_depth == 1:
                palette[0] = 0xFFFFFF
                palette[1] = 0x000000
            elif self.color_depth == 4:
                for i, rgb in enumerate(_ACEP_PALETTE_RGB):
                    palette[i] = rgb
                for i in range(len(_ACEP_PALETTE_RGB), colors):
                    palette[i] = 0xFFFFFF
            else:
                palette[0] = 0xFFFFFF
                palette[1] = 0x000000
                palette[2] = 0xFF0000
                palette[3] = 0x888888
            tile = displayio.TileGrid(bitmap, pixel_shader=palette)
            group = displayio.Group()
            group.append(tile)
            self._displayio_group = group
            self._displayio_bitmap = bitmap
            self._displayio_palette = palette

        bitmap = self._displayio_bitmap
        inverted = getattr(self._epaper, "black_bits_inverted", False)
        for y in range(self.height):
            for x in range(self.width):
                value = self._get_packed_pixel(x, y)
                if self.color_depth == 1 and inverted:
                    value = 1 - value
                bitmap[x, y] = value
        self._epaper.root_group = self._displayio_group

    def _push_buffer_bus(self):
        ep = self._epaper
        bus = getattr(ep, "bus", None)
        write_black = getattr(ep, "write_black_ram_command", None)
        if bus is None or write_black is None or self._buffer is None:
            return False

        self._send_ram_window(ep, bus)

        write_color = getattr(ep, "write_color_ram_command", None)
        if write_color is not None and self.color_depth == 2:
            black, color = self._tri_color_planes()
            if getattr(ep, "black_bits_inverted", False):
                black = bytes(b ^ 0xFF for b in black)
            if getattr(ep, "color_bits_inverted", False):
                color = bytes(b ^ 0xFF for b in color)
            bus.send(write_black, black)
            bus.send(write_color, color)
            return True

        data = self._panel_buffer()
        if getattr(ep, "black_bits_inverted", False) and self.color_depth == 1:
            data = bytes(b ^ 0xFF for b in data)
        bus.send(write_black, data)
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
