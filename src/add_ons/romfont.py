"""
Read a raw binary font file and creates a Framebuffer font object.
"""

from graphics import MONO_HLSB, RGB565, Area, FrameBuffer


class ROMFont:
    def __init__(self, font_file):
        """
        Create a new ROMFont object.  The font file is a raw binary file containing
        256 characters.  Each character is 8 pixels wide and any number of pixels high.

        Args:
            font_file (str): The path to the raw binary font file.

        Usage:
            font = ROMFont("fontfile.bin")
            font.text(canvas, "Hello", 0, 0, 1)
        """
        with open(font_file, "rb") as f:
            raw = f.read()
        self.buffer = memoryview(raw)
        self.char_width = 8
        self.char_height = len(self.buffer) // 256

    def char(self, canvas: FrameBuffer, c, x, y, key=-1, pal=None):
        """
        Place a character on the canvas.

        Args:
            canvas (FrameBuffer): The canvas to draw on.
            c (str): The character to draw.
            x (int): The x coordinate.
            y (int): The y coordinate.
            key (int): The color key.
            pal (FrameBuffer): The palette to use.

        Returns:
            (Area): The area of the canvas that was drawn on.
        """
        # create a memoryview of the character in the font
        offset = ord(c) * self.char_height
        char_view = self.buffer[offset : offset + self.char_height]
        canvas.blit(
            FrameBuffer(char_view, self.char_width, self.char_height, MONO_HLSB), x, y, key, pal
        )
        return Area(x, y, self.char_width, self.char_height)

    def text(self, canvas, s, x, y, fg, bg=None):
        """
        Place text on the canvas.  Breaks on \n to next line.

        Does not break on line going off canvas.

        Args:
            canvas (Canvas): The DisplayDriver, FrameBuffer, or other canvas-like object to draw on.
            s (str): The text to draw.
            x (int): The x coordinate.
            y (int): The y coordinate.
            fg (int): The foreground color.
            bg (int): The background color.

        Returns:
            Area: The area of the canvas that was drawn on.
        """
        pal = FrameBuffer(memoryview(bytearray(4)), 2, 1, RGB565)
        if bg is None:
            bg = key = ~fg
        else:
            key = -1
        pal.pixel(0, 0, bg)
        pal.pixel(1, 0, fg)

        x_pos = x
        y_pos = y

        area = self.char(canvas, s[0], x_pos, y_pos, key, pal)
        x_pos += self.char_width
        for char in s[1:]:
            if char == "\n":
                y_pos += self.char_height
                x_pos = x
                continue
            area += self.char(canvas, char, x_pos, y_pos, key, pal)
            x_pos += self.char_width
        return area
