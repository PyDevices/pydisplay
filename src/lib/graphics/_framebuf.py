# SPDX-FileCopyrightText: <text> 2018 Kattni Rembor, Melissa LeBlanc-Williams
# and Tony DiCola, for Adafruit Industries.
# Copyright 2024 Brad Barnett
# Original file created by Damien P. George
# SPDX-License-Identifier: MIT

"""
`graphics._framebuf`
====================================================

*Python framebuf module, based on the micropython framebuf module.
Will not be imported on MicroPython boards since framebuf is included
in the compiled firmware.

framebuf on MicroPython does not return an Area object for methods that
write to the buffer, but BasicShapes does, so the native shape methods
here return an Area object in order to keep it consistent within this
library.  It is recommended to use framebuf_plus.py instead of this if
you need to use the returned Areas so your code will be transferable.

"""

from . import _shapes
from . import _font

try:
    from ulab import numpy as np
except ImportError:
    try:
        import numpy as np
    except ImportError:
        np = None


# Framebuf format constants:
MONO_VLSB = 0
MONO_HLSB = 3
MONO_HMSB = 4
RGB565 = 1
GS2_HMSB = 5
GS4_HMSB = 2
GS8 = 6


class MVLSBFormat:
    depth = 1

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        index = (y >> 3) * framebuf._stride + x
        offset = y & 0x07
        framebuf._buffer[index] = (framebuf._buffer[index] & ~(0x01 << offset)) | (
            (color != 0) << offset
        )

    @staticmethod
    def get_pixel(framebuf, x, y):
        index = (y >> 3) * framebuf._stride + x
        offset = y & 0x07
        return (framebuf._buffer[index] >> offset) & 0x01

    @staticmethod
    def fill(framebuf, color):
        if color:
            fill = 0xFF
        else:
            fill = 0x00
        for i in range(len(framebuf._buffer)):  # pylint: disable=consider-using-enumerate
            framebuf._buffer[i] = fill

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        while height > 0:
            index = (y >> 3) * framebuf._stride + x
            offset = y & 0x07
            for w_w in range(width):
                framebuf._buffer[index + w_w] = (
                    framebuf._buffer[index + w_w] & ~(0x01 << offset)
                ) | ((color != 0) << offset)
            y += 1
            height -= 1


class MHLSBFormat:
    depth = 1

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        index = (y * framebuf._stride + x) >> 3
        offset = 7 - (x & 0x07)
        framebuf._buffer[index] = (framebuf._buffer[index] & ~(0x01 << offset)) | (
            (color != 0) << offset
        )

    @staticmethod
    def get_pixel(framebuf, x, y):
        index = (x + y * framebuf._stride) >> 3
        offset = 7 - (x & 0x07)
        return (framebuf._buffer[index] >> offset) & 0x01

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        for _x in range(x, x + width):
            offset = 7 - _x & 0x07
            for _y in range(y, y + height):
                index = (_y * framebuf._stride + _x) >> 3
                framebuf._buffer[index] = (framebuf._buffer[index] & ~(0x01 << offset)) | (
                    (color != 0) << offset
                )

    @staticmethod
    def fill(framebuf, color):
        if color:
            fill = 0xFF
        else:
            fill = 0x00
        for i in range(len(framebuf._buffer)):
            framebuf._buffer[i] = fill


class MHMSBFormat:
    depth = 1

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        index = (y * framebuf._stride + x) >> 3
        offset = x & 0x07
        framebuf._buffer[index] = (framebuf._buffer[index] & ~(0x01 << offset)) | (
            (color != 0) << offset
        )

    @staticmethod
    def get_pixel(framebuf, x, y):
        index = (y * framebuf._stride + x) // 8
        offset = 7 - x & 0x07
        return (framebuf._buffer[index] >> offset) & 0x01

    @staticmethod
    def fill(framebuf, color):
        if color:
            fill = 0xFF
        else:
            fill = 0x00
        for i in range(len(framebuf._buffer)):  # pylint: disable=consider-using-enumerate
            framebuf._buffer[i] = fill

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        for _x in range(x, x + width):
            offset = 7 - _x & 0x07
            for _y in range(y, y + height):
                index = (_y * framebuf._stride + _x) // 8
                framebuf._buffer[index] = (framebuf._buffer[index] & ~(0x01 << offset)) | (
                    (color != 0) << offset
                )


class GS2HMSBFormat:
    depth = 2

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        index = (y * framebuf._stride + x) >> 2
        pixel = framebuf._buffer[index]

        shift = (x & 0b11) << 1
        mask = 0b11 << shift
        color = (color & 0b11) << shift

        framebuf._buffer[index] = color | (pixel & (~mask))

    @staticmethod
    def get_pixel(framebuf, x, y):
        index = (y * framebuf._stride + x) >> 2
        pixel = framebuf._buffer[index]

        shift = (x & 0b11) << 1
        return (pixel >> shift) & 0b11

    @staticmethod
    def fill(framebuf, color):
        if color:
            bits = color & 0b11
            fill = (bits << 6) | (bits << 4) | (bits << 2) | (bits << 0)
        else:
            fill = 0x00

        framebuf._buffer = [fill for i in range(len(framebuf._buffer))]

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        """Draw the outline and interior of a rectangle at the given location, size and color."""
        # pylint: disable=too-many-arguments
        for _x in range(x, x + width):
            for _y in range(y, y + height):
                GS2HMSBFormat.set_pixel(framebuf, _x, _y, color)


class GS4HMSBFormat:
    depth = 4

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        raise NotImplementedError

    @staticmethod
    def get_pixel(framebuf, x, y):
        raise NotImplementedError

    @staticmethod
    def fill(framebuf, color):
        raise NotImplementedError

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        raise NotImplementedError


class GS8Format:
    depth = 8

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        index = y * framebuf._stride + x
        framebuf._buffer[index] = color.to_bytes(1, "little")

    @staticmethod
    def get_pixel(framebuf, x, y):
        index = y * framebuf._stride + x
        return int.from_bytes(framebuf._buffer[index : index + 1], "little")

    @staticmethod
    def fill(framebuf, color):
        framebuf._buffer = color.to_bytes(1, "little") * len(framebuf._buffer)

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        color = color.to_bytes(1, "little")
        for _y in range(y, y + height):
            offset = _y * framebuf._stride
            for _x in range(x, x + width):
                index = offset + _x
                framebuf._buffer[index] = color


class RGB565Format:
    depth = 16

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        index = (y * framebuf._stride + x) * 2
        framebuf._buffer[index : index + 2] = (color & 0xFFFF).to_bytes(2, "little")

    @staticmethod
    def get_pixel(framebuf, x, y):
        index = (y * framebuf._stride + x) * 2
        color = framebuf._buffer[index : index + 2]
        color = int.from_bytes(color, "little")
        return color

    @staticmethod
    def fill(framebuf, color):
        rgb565_color = (color & 0xFFFF).to_bytes(2, "little")
        for i in range(0, len(framebuf._buffer), 2):
            framebuf._buffer[i : i + 2] = rgb565_color

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        # make sure x, y, width, height are within the bounds of the framebuf
        if x < 0:
            width += x
            x = 0
        if y < 0:
            height += y
            y = 0
        if x + width > framebuf.width:
            width = framebuf.width - x
        if y + height > framebuf.height:
            height = framebuf.height - y
        stride = framebuf._stride
        rgb565_color = (color & 0xFFFF).to_bytes(2, "little")
        if np:
            rgb565_color_int = int.from_bytes(rgb565_color, "little")
            arr = np.frombuffer(framebuf._buffer, dtype=np.uint16)
            for _y in range(y, y + height):
                arr[_y * stride + x : _y * stride + x + width] = rgb565_color_int
        else:
            for _y in range(y, y + height):
                offset = _y * stride
                for _x in range(x, x + width):
                    index = (offset + _x) * 2
                    framebuf._buffer[index : index + 2] = rgb565_color


class FrameBuffer:
    """
    FrameBuffer object.

    Args:
        buffer (bytearray): The buffer to use for the frame buffer.
        width (int): The width of the frame buffer in pixels.
        height (int): The height of the frame buffer in pixels.
        format (int): The format of the frame buffer. One of:
            - ``MONO_VLSB``: Single bit displays (like SSD1306 OLED)
            - ``MONO_HLSB``: Single bit files like PBM (Portable BitMap)
            - ``MONO_HMSB``: Single bit displays where the bits in a byte are horizontally mapped
                Each byte occupies 8 horizontal pixels with bit 0 being the leftmost.
            - ``RGB565``: 16-bit color displays
            - ``GS2_HMSB``: 2-bit color displays like the HT16K33 8x8 Matrix
            - ``GS4_HMSB``: Unimplemented!
            - ``GS8``: Unimplemented!
        stride (int): The number of bytes between each horizontal line of the frame buffer
            If not given, it is assumed to be equal to the width.
    """

    def __init__(self, buffer, width, height, format, stride=None):
        self._buffer = buffer
        self._width = width
        self._height = height
        self._stride = stride if stride is not None else width
        self._font = None
        if format == MONO_VLSB:
            self._stride = (self._stride + 7) & ~7
            self._format = MVLSBFormat()
        elif format == MONO_HLSB:
            self._stride = (self._stride + 7) & ~7
            self._format = MHLSBFormat()
        elif format == MONO_HMSB:
            self._format = MHMSBFormat()
        elif format == RGB565:
            self._format = RGB565Format()
        elif format == GS2_HMSB:
            self._stride = (self._stride + 3) & ~3
            self._format = GS2HMSBFormat()
        elif format == GS4_HMSB:
            self._stride = (self._stride + 1) & ~1
            self._format = GS4HMSBFormat()
        elif format == GS8:
            self._format = GS8Format()
        else:
            raise ValueError("invalid format")

    @property
    def width(self):
        """
        The width of the FrameBuffer in pixels.
        """
        return self._width

    @property
    def height(self):
        """
        The height of the FrameBuffer in pixels.
        """
        return self._height

    def fill_rect(self, x, y, w, h, c):
        """
        Draw a rectangle at the given location, size and color.

        Args:
            x (int): The x-coordinate of the top left corner of the rectangle.
            y (int): The y-coordinate of the top left corner of the rectangle.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.
            c (int): The color of the rectangle.

        Returns:
            (tuple): A tuple containing the x, y, width, and height of the rectangle
        """
        self._format.fill_rect(self, x, y, w, h, c)
        return (x, y, w, h)

    def pixel(self, x, y, c=None):
        """
        Set or get the color of a given pixel.

        Args:
            x (int): The x-coordinate of the pixel.
            y (int): The y-coordinate of the pixel.
            c (int): The color of the pixel. If not given, the color of the pixel is returned.

        Returns:
            (int, tuple or None):  If c is not given, the color of the pixel is returned.
                If c is given and x and y are within the bounds of the FrameBuffer,
                the x, y, width, and height of the pixel are returned.
                If x and y are not within the bounds of the FrameBuffer, None is returned.
        """
        if x < 0 or x >= self._width or y < 0 or y >= self._height:
            return None
        if c is None:
            return self._format.get_pixel(self, x, y)
        self._format.set_pixel(self, x, y, c)
        return (x, y, 1, 1)

    def fill(self, c):
        """
        Fill the entire FrameBuffer with the specified color.

        Args:
            c (int): The color to fill the FrameBuffer with.

        Returns:
            (tuple): A tuple containing the x, y, width, and height of the FrameBuffer.
        """
        self._format.fill(self, c)
        return (0, 0, self._width, self._height)

    def scroll(self, xstep, ystep):
        """
        Shift the contents of the FrameBuffer by the given vector (xstep, ystep).
        This may leave a footprint of the previous colors in the FrameBuffer.

        Args:
            xstep (int): The number of pixels to shift the FrameBuffer in the x direction.
            ystep (int): The number of pixels to shift the FrameBuffer in the y direction.

        Raises:
            ValueError: If the FrameBuffer format depth is not a multiple of 8
        """
        # Check to make sure self._format.depth is a multiple of 8
        if self._format.depth % 8 != 0:
            raise ValueError("Scrolling is only implemented for depths that are multiples of 8")

        BPP = self._format.depth // 8  # Bytes per pixel

        # Determine the width and height of the FrameBuffer
        width = self._width
        height = self._height

        # Calculate the number of bytes per row
        bytes_per_row = width * BPP

        # Iterate over each row in the appropriate order (top to bottom for ystep > 0, bottom to top for ystep < 0)
        if ystep > 0:
            y_range = range(height - 1, -1, -1)
        else:
            y_range = range(height)

        # Iterate over each row in the appropriate order
        for y in y_range:
            # Calculate the new row index
            new_y = y + ystep

            # Skip rows that go out of bounds
            if new_y < 0 or new_y >= height:
                continue

            # Calculate the byte offset for the current and new rows
            offset = y * bytes_per_row
            new_offset = new_y * bytes_per_row

            # Iterate over each column in the appropriate order (right to left for xstep > 0, left to right for xstep < 0)
            if xstep > 0:
                for i in range(bytes_per_row - 1, (xstep * BPP) - 1, -1):
                    self._buffer[new_offset + i] = self._buffer[offset + i - (xstep * BPP)]
            elif xstep < 0:
                for i in range(-xstep * BPP, bytes_per_row):
                    self._buffer[new_offset + i] = self._buffer[offset + i + (xstep * BPP)]
            else:
                # If there is no x shift, copy the row as is
                self._buffer[new_offset : new_offset + bytes_per_row] = self._buffer[
                    offset : offset + bytes_per_row
                ]

    def blit(self, *args, **kwargs):
        """
        Blit a source to the canvas at the specified x, y location.

        Args:
            source (FrameBuffer): Source FrameBuffer object.
            x (int): X-coordinate to blit to.
            y (int): Y-coordinate to blit to.
            key (int): Key value for transparency (default: -1).
            palette (Palette): Palette object for color translation (default: None).
        """
        _shapes.blit(self, *args, **kwargs)

    def ellipse(self, *args, **kwargs):
        """
        Midpoint ellipse algorithm
        Draw an ellipse at the given location. Radii r1 and r2 define the geometry; equal values cause a
        circle to be drawn. The c parameter defines the color.

        The optional f parameter can be set to True to fill the ellipse. Otherwise just a one pixel outline
        is drawn.

        The optional m parameter enables drawing to be restricted to certain quadrants of the ellipse.
        The LS four bits determine which quadrants are to be drawn, with bit 0 specifying Q1, b1 Q2,
        b2 Q3 and b3 Q4. Quadrants are numbered counterclockwise with Q1 being top right.

        Args:
            x0 (int): Center x coordinate
            y0 (int): Center y coordinate
            r1 (int): x radius
            r2 (int): y radius
            c (int): color
            f (bool): Fill the ellipse (default: False)
            m (int): Bitmask to determine which quadrants to draw (default: 0b1111)
            w (int): Width of the ellipse (default: None)
            h (int): Height of the ellipse (default: None)
        """
        _shapes.ellipse(self, *args, **kwargs)

    def hline(self, *args, **kwargs):
        """
        Horizontal line drawing function.  Will draw a single pixel wide line.

        Args:
            x0 (int): X-coordinate of the start of the line.
            y0 (int): Y-coordinate of the start of the line.
            w (int): Width of the line.
            c (int): color.
        """
        _shapes.hline(self, *args, **kwargs)

    def line(self, *args, **kwargs):
        """
        Line drawing function.  Will draw a single pixel wide line starting at
        x0, y0 and ending at x1, y1.

        Args:
            x0 (int): X-coordinate of the start of the line.
            y0 (int): Y-coordinate of the start of the line.
            x1 (int): X-coordinate of the end of the line.
            y1 (int): Y-coordinate of the end of the line.
            c (int): color.
        """
        _shapes.line(self, *args, **kwargs)

    def poly(self, *args, **kwargs):
        """
        Given a list of coordinates, draw an arbitrary (convex or concave) closed polygon at the given x, y location
        using the given color.

        The coords must be specified as an array of integers, e.g. array('h', [x0, y0, x1, y1, ... xn, yn]) or a
        list or tuple of points, e.g. [(x0, y0), (x1, y1), ... (xn, yn)].

        The optional f parameter can be set to True to fill the polygon. Otherwise, just a one-pixel outline is drawn.

        Args:
            x (int): X-coordinate of the polygon's position.
            y (int): Y-coordinate of the polygon's position.
            coords (list): List of coordinates.
            c (int): color.
            f (bool): Fill the polygon (default: False).
        """
        _shapes.poly(self, *args, **kwargs)

    def rect(self, *args, **kwargs):
        """
        Rectangle drawing function.  Will draw a single pixel wide rectangle starting at
        x0, y0 and extending w, h pixels.

        Args:
            x0 (int): X-coordinate of the top-left corner of the rectangle.
            y0 (int): Y-coordinate of the top-left corner of the rectangle.
            w (int): Width of the rectangle.
            h (int): Height of the rectangle.
            c (int): color.
            f (bool): Fill the rectangle (default: False).
        """
        _shapes.rect(self, *args, **kwargs)

    def vline(self, *args, **kwargs):
        """
        Horizontal line drawing function.  Will draw a single pixel wide line.

        Args:
            x0 (int): X-coordinate of the start of the line.
            y0 (int): Y-coordinate of the start of the line.
            h (int): Height of the line.
            c (int): color.
        """
        _shapes.vline(self, *args, **kwargs)

    def text(self, *args, **kwargs):
        """
        Place text on the canvas with an 8 pixel high font.
        Breaks on \n to next line.  Does not break on line going off canvas.

        Args:
            s (str): The text to draw.
            x (int): The x position to start drawing the text.
            y (int): The y position to start drawing the text.
            c (int): The color to draw the text in.  Default is 1.
            scale (int): The scale factor to draw the text at.  Default is 1.
            inverted (bool): If True, draw the text inverted.  Default is False.
            font_data (str): The path to the font file to use.  Default is None.
        """
        _font.text(self, *args, **kwargs)


def FrameBuffer1(buffer, width, height, format, stride=None):
    """
    Create a new FrameBuffer object.  Here only for historical reasons.
    """
    return FrameBuffer(buffer, width, height, format, stride)
