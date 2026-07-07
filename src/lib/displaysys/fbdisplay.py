# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.fbdisplay
"""

from displaysys import DisplayDriver


class FBDisplay(DisplayDriver):
    """
    A class to interface with CircuitPython FrameBuffer objects.

    Args:
        buffer (FrameBuffer): The CircuitPython FrameBuffer object.
        width (int, optional): The width of the display. Defaults to None.
        height (int, optional): The height of the display. Defaults to None.
        reverse_bytes_in_word (bool, optional): Whether to reverse the bytes in a word. Defaults to False.

    Attributes:
        color_depth (int): The color depth of the display
    """

    def __init__(self, buffer, width=None, height=None, reverse_bytes_in_word=False):
        self._raw_buffer = buffer
        self._buffer = memoryview(buffer)
        self._width = width if width else buffer.width
        self._height = height if height else buffer.height
        self._requires_byteswap = reverse_bytes_in_word
        self._rotation = 0
        self.color_depth = 16

        super().__init__()

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
        BPP = self.color_depth // 8
        if self._auto_byteswap:
            color_bytes = (c & 0xFFFF).to_bytes(2, "big")
        else:
            color_bytes = (c & 0xFFFF).to_bytes(2, "little")

        for _y in range(y, y + h):
            begin = (_y * self.width + x) * BPP
            end = begin + w * BPP
            self._buffer[begin:end] = color_bytes * w
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
        for row in range(h):
            source_begin = row * w * BPP
            source_end = source_begin + w * BPP
            dest_begin = ((y + row) * self.width + x) * BPP
            dest_end = dest_begin + w * BPP
            self._buffer[dest_begin:dest_end] = buf[source_begin:source_end]
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
        """
        self._raw_buffer.refresh()
