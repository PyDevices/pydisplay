# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.fbdisplay
"""

from displaysys import DisplayDriver


def _as_u16_pixels(buf):
    """View RGB565 byte data as uint16 pixels (little-endian) for bitmaptools."""
    mv = memoryview(buf)
    try:
        return mv.cast("H")
    except (AttributeError, TypeError, ValueError):
        import array

        return array.array("H", mv)


class FBDisplay(DisplayDriver):
    """
    A class to interface with CircuitPython FrameBuffer objects.

    Args:
        buffer (FrameBuffer): The CircuitPython FrameBuffer object
            (e.g. ``dotclockframebuffer.DotClockFramebuffer``, already in PSRAM).
        width (int, optional): The width of the display. Defaults to None.
        height (int, optional): The height of the display. Defaults to None.
        reverse_bytes_in_word (bool, optional): Whether to reverse the bytes in a word. Defaults to False.
        bitmap: Optional ``displayio.Bitmap`` paint surface (typically allocated in
            SPIRAM/PSRAM). When set with ``bitmaptools``, blit/fill use C
            ``arrayblit`` / ``fill_region`` — the Adafruit Qualia RGB666 path —
            instead of Python loops into the raw framebuffer.
        display: Optional ``framebufferio.FramebufferDisplay`` that owns ``bitmap``
            as its root group. ``show()`` calls ``display.refresh()`` so dirty
            regions are composited in C into the DotClock PSRAM framebuffer.

    Attributes:
        color_depth (int): The color depth of the display
    """

    def __init__(
        self,
        buffer,
        width=None,
        height=None,
        reverse_bytes_in_word=False,
        *,
        bitmap=None,
        display=None,
        quiet=False,
    ):
        self._raw_buffer = buffer
        mv = memoryview(buffer)
        self._width = width if width else buffer.width
        self._height = height if height else buffer.height
        self._requires_byteswap = reverse_bytes_in_word
        self._rotation = 0
        self.color_depth = 16
        self._bitmap = bitmap
        self._display = display
        self._bitmaptools = None
        if bitmap is not None:
            try:
                import bitmaptools as _bt

                self._bitmaptools = _bt
            except ImportError:
                self._bitmap = None

        # Native framebuffers may expose RGB565 as bytes ('B') or uint16 ('H').
        # DotClockFramebuffer on CircuitPython is uint16-indexed (len == pixels);
        # painting through that view is a Python per-pixel loop (~12s for 720x720).
        # Prefer a byte view so blit/fill can use bulk memoryview assigns when no
        # displayio.Bitmap is provided.
        pix = self._width * self._height
        self._buffer_u16 = len(mv) == pix
        self._buffer = mv
        self._pixel_bytes = mv
        if self._buffer_u16:
            try:
                self._pixel_bytes = mv.cast("B")
            except (AttributeError, TypeError, ValueError):
                # No cast: fall back to slow uint16 element stores in blit/fill.
                self._pixel_bytes = None

        super().__init__(quiet=quiet)

    ############### Required API Methods ################

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """

    def fill_rect(self, x, y, w, h, c):
        """
        Fills a rectangle with the given color.

        Args:
            x (int): The x-coordinate of the top-left corner of the rectangle.
            y (int): The y-coordinate of the top-left corner of the rectangle.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.
            c (int): The color to fill the rectangle with.

        Returns:
            (tuple): A tuple containing the x, y, w, h values
        """
        color = c & 0xFFFF
        bt = self._bitmaptools
        if bt is not None and self._bitmap is not None:
            # C fill into PSRAM Bitmap (Adafruit Qualia path).
            if self._auto_byteswap:
                color = ((color & 0xFF) << 8) | (color >> 8)
            bt.fill_region(self._bitmap, x, y, x + w, y + h, color)
            return (x, y, w, h)

        dest = self._pixel_bytes
        if dest is None:
            # uint16 buffer without byte cast — last-resort element stores.
            if self._auto_byteswap:
                color = ((color & 0xFF) << 8) | (color >> 8)
            buf = self._buffer
            for _y in range(y, y + h):
                begin = _y * self.width + x
                end = begin + w
                for i in range(begin, end):
                    buf[i] = color
            return (x, y, w, h)

        BPP = self.color_depth // 8
        if self._auto_byteswap:
            color_bytes = color.to_bytes(2, "big")
        else:
            color_bytes = color.to_bytes(2, "little")

        # Full-width: contiguous band assigns. A single ``color_bytes * (w*h)`` for
        # 720x720 is ~1MB and can OOM on CircuitPython; chunked bands stay small
        # while avoiding per-row slice assigns (~60ms/row into DotClockFramebuffer).
        if x == 0 and w == self.width:
            band_rows = min(h, 48)
            block = color_bytes * (w * band_rows)
            y0 = y
            left = h
            while left:
                rows = band_rows if left >= band_rows else left
                if rows != band_rows:
                    block = color_bytes * (w * rows)
                begin = y0 * self.width * BPP
                dest[begin : begin + len(block)] = block
                y0 += rows
                left -= rows
            return (x, y, w, h)

        rowbytes = color_bytes * w
        for _y in range(y, y + h):
            begin = (_y * self.width + x) * BPP
            end = begin + w * BPP
            dest[begin:end] = rowbytes
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        """
        Blits a buffer to the display at the given coordinates.

        Args:
            buf (memoryview): The buffer to blit.
            x (int): The x-coordinate of the buffer.
            y (int): The y-coordinate of the buffer.
            w (int): The width of the buffer.
            h (int): The height of the buffer.

        Returns:
            (tuple): A tuple containing the x, y, w, h values.
        """
        if self._auto_byteswap:
            self.byteswap(buf)

        BPP = self.color_depth // 8
        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            raise ValueError("The provided x, y, w, h values are out of range")
        if len(buf) != w * h * BPP:
            raise ValueError("The source buffer is not the correct size")

        bt = self._bitmaptools
        if bt is not None and self._bitmap is not None:
            # C arrayblit into PSRAM Bitmap — same idea as Adafruit's Qualia demos
            # (paint Bitmap; FramebufferDisplay composites into DotClock PSRAM).
            bt.arrayblit(self._bitmap, _as_u16_pixels(buf), x, y, x + w, y + h)
            return (x, y, w, h)

        dest = self._pixel_bytes
        if dest is None:
            # Source is byte-packed RGB565; dest buffer is uint16 elements.
            src = memoryview(buf)
            for row in range(h):
                for col in range(w):
                    i = (row * w + col) * 2
                    color = src[i] | (src[i + 1] << 8)
                    self._buffer[(y + row) * self.width + x + col] = color
            return (x, y, w, h)

        # Native FB blit (mipidsi on ESP32-P4): Python memoryview row slices into
        # SPIRAM are ~25ms/row; C memcpy is sub-millisecond for LVGL partials.
        native_blit = getattr(self._raw_buffer, "blit", None)
        if native_blit is not None:
            native_blit(buf, x, y, w, h)
            return (x, y, w, h)

        # Contiguous copy for full-width strips (and full frames). Per-row
        # memoryview slice assigns into some native FBs (e.g. mipidsi on
        # ESP32-P4 720x720) are ~28ms/row — a height/10 LVGL partial was ~2s.
        if x == 0 and w == self.width:
            begin = y * self.width * BPP
            dest[begin : begin + h * self.width * BPP] = buf
            return (x, y, w, h)

        for row in range(h):
            source_begin = row * w * BPP
            source_end = source_begin + w * BPP
            dest_begin = ((y + row) * self.width + x) * BPP
            dest_end = dest_begin + w * BPP
            dest[dest_begin:dest_end] = buf[source_begin:source_end]
        return (x, y, w, h)

    def pixel(self, x, y, c):
        """
        Sets the color of the pixel at the given coordinates.

        Args:
            x (int): The x-coordinate of the pixel.
            y (int): The y-coordinate of the pixel.
            c (int): The color of the pixel.

        Returns:
            (tuple): A tuple containing the x, y values.
        """
        return self.fill_rect(x, y, 1, 1, c)

    ############### Optional API Methods ################

    def show(self, _timer=None) -> None:
        """
        Refreshes the display.

        When a ``FramebufferDisplay`` is in ``auto_refresh`` mode (Adafruit
        Qualia / DotClock), skip manual refresh — paced background refresh
        avoids tearing against the continuous DPI scanout. Manual
        ``refresh()`` every LVGL tick was the flicker source.
        """
        disp = self._display
        if disp is not None:
            if getattr(disp, "auto_refresh", False):
                return
            try:
                disp.refresh()
                return
            except TypeError:
                try:
                    disp.refresh(None, None)
                    return
                except Exception:
                    pass
        self._raw_buffer.refresh()
