from ._area import Area
from . import _shapes
from . import _files
from . import _font

try:  # Try to import framebuf from MicroPython
    from framebuf import (
        MONO_VLSB,
        MONO_HLSB,
        MONO_HMSB,
        GS2_HMSB,
        GS4_HMSB,
        GS8,
        RGB565,
        FrameBuffer as _FrameBuffer,
    )
except ImportError:  # If framebuf is not available, import from _framebuf.py
    from ._framebuf import (
        MONO_VLSB,
        MONO_HLSB,
        MONO_HMSB,
        GS2_HMSB,
        GS4_HMSB,
        GS8,
        RGB565,
        FrameBuffer as _FrameBuffer,
    )


class FrameBuffer(_FrameBuffer):
    """
    An extension of MicroPython's framebuf.FrameBuffer that adds some useful methods for drawing shapes and text.
    Each method returns a bounding box (x, y, w, h) of the drawn shape to indicate
    the area of the display that was modified.  This can be used to update only the
    modified area of the display.  Exposes attributes not exposed in the base class, such
    as color_depth, width, height, buffer, and format.  Also adds a save method to save
    the framebuffer to a file, and a from_file method to load a framebuffer from a file.

    Inherits from frambuf.Framebuffer, which may be compiled into MicroPython
    or may be from _framebuf.py.  Methods should return an Area object, but
    the MicroPython framebuf module returns None, so the methods inherited from
    framebuf.FrameBuffer are overridden to return an Area object.

    Args:
        buffer (bytearray): Framebuffer buffer
        width (int): Width in pixels
        height (int): Height in pixels
        format (int): Framebuffer format

    Attributes:
        buffer (bytearray): Framebuffer buffer
        width (int): Width in pixels
        height (int): Height in pixels
        format (int): Framebuffer format
        color_depth (int): Color depth
    """

    def __init__(self, buffer, width, height, format, *args, **kwargs):
        super().__init__(buffer, width, height, format, *args, **kwargs)
        self._width = width
        self._height = height
        self._fb_format = format
        self._buffer = buffer
        if format == MONO_VLSB:
            self._color_depth = 1
        elif format == MONO_HLSB:
            self._color_depth = 1
        elif format == MONO_HMSB:
            self._color_depth = 1
        elif format == RGB565:
            self._color_depth = 16
        elif format == GS2_HMSB:
            self._color_depth = 2
        elif format == GS4_HMSB:
            self._color_depth = 4
        elif format == GS8:
            self._color_depth = 8
        else:
            raise ValueError("invalid format")

    @property
    def color_depth(self):
        return self._color_depth

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def buffer(self):
        return self._buffer

    @property
    def format(self):
        return self._fb_format

    def fill_rect(self, x, y, w, h, c):
        """
        Fill the given rectangle with the given color.

        Args:
            x (int): x coordinate
            y (int): y coordinate
            w (int): Width in pixels
            h (int): Height in pixels
            c (int): color

        Returns:
            (Area): Bounding box of the filled rectangle
        """
        super().fill_rect(x, y, w, h, c)
        return Area(x, y, w, h)

    def pixel(self, x, y, c=None):
        """
        Draw a single pixel at the given location and color.

        Args:
            x (int): x coordinate
            y (int): y coordinate
            c (int): color (default: None)

        Returns:
            (Area): Bounding box of the pixel
        """
        if c is None:
            return super().pixel(x, y)
        super().pixel(x, y, c)
        return Area(x, y, 1, 1)

    def fill(self, c):
        """
        Fill the buffer with the given color.

        Args:
            c (int): color

        Returns:
            (Area): Bounding box of the filled buffer
        """
        super().fill(c)
        return Area(0, 0, self.width, self.height)

    def ellipse(self, x, y, rx, ry, c, f=False, m=0b1111):
        """
        Draw an ellipse at the given location, radii and color.

        Args:
            x (int): Center x coordinate
            y (int): Center y coordinate
            rx (int): X radius
            ry (int): Y radius
            c (int): color
            f (bool): Fill the ellipse (default: False)
            m (int): Bitmask to determine which quadrants to draw (default: 0b1111)

        Returns:
            (Area): Bounding box of the ellipse
        """
        super().ellipse(x, y, rx, ry, c, f, m)
        return Area(x - rx, y - ry, 2 * rx, 2 * ry)

    def hline(self, x, y, w, c):
        """
        Draw a horizontal line at the given location, width and color.

        Args:
            x (int): x coordinate
            y (int): y coordinate
            w (int): Width in pixels
            c (int): color

        Returns:
            (Area): Bounding box of the horizontal line
        """
        super().hline(x, y, w, c)
        return Area(x, y, w, 1)

    def line(self, x1, y1, x2, y2, c):
        """
        Draw a line between the given start and end points and color.

        Args:
            x1 (int): Start x coordinate
            y1 (int): Start y coordinate
            x2 (int): End x coordinate
            y2 (int): End y coordinate
            c (int): color

        Returns:
            (Area): Bounding box of the line
        """
        super().line(x1, y1, x2, y2, c)
        return Area(min(x1, x2), min(y1, y2), abs(x2 - x1) + 1, abs(y2 - y1) + 1)

    def poly(self, x, y, coords, c, f=False):
        """
        Draw a polygon at the given location, coordinates and color.

        Args:
            x (int): x coordinate
            y (int): y coordinate
            coords (array): Array of x, y coordinate tuples
            c (int): color
            f (bool): Fill the polygon (default: False)

        Returns:
            (Area): Bounding box of the polygon
        """
        super().poly(x, y, coords, c, f)
        # Calculate the bounding box of the polygon
        # Convert the coords to a list of x, y tuples if it is not already
        if isinstance(coords, list):
            vertices = coords
        elif isinstance(coords, tuple):
            vertices = list(coords)
        else:
            # Check that the coords array has an even number of elements
            if len(coords) % 2 != 0:
                raise ValueError("coords must have an even number of elements")
            vertices = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
        # Find the min and max x and y values
        min_x = min([v[0] for v in vertices])
        min_y = min([v[1] for v in vertices])
        max_x = max([v[0] for v in vertices])
        max_y = max([v[1] for v in vertices])
        return Area(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

    def rect(self, x, y, w, h, c, f=False):
        """
        Draw a rectangle at the given location, size and color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            w (int): Width in pixels
            h (int): Height in pixels
            c (int): color
            f (bool): Fill the rectangle (default: False)

        Returns:
            (Area): Bounding box of the rectangle
        """
        super().rect(x, y, w, h, c, f)
        return Area(x, y, w, h)

    def vline(self, x, y, h, c):
        """
        Draw a vertical line at the given location, height and color.

        Args:
            x (int): x coordinate
            y (int): y coordinate
            h (int): Height in pixels
            c (int): color

        Returns:
            (Area): Bounding box of the vertical line
        """
        super().vline(x, y, h, c)
        return Area(x, y, 1, h)

    def text(self, s, x, y, c=1, scale=1, inverted=False, font_data=None, height=8):
        """
        Draw text at the given location, using the given font and color.

        Args:
            s (str): Text to draw
            x (int): x coordinate
            y (int): y coordinate
            c (int): color
            scale (int): Scale factor (default: 1)
            inverted (bool): Invert the text (default: False)
            font_data (str): Path to the font file (default: None)
            height (int): Height of the font (default: 8)

        Returns:
            (Area): Bounding box of the text
        """
        return _font.text(
            self, s, x, y, c, scale=scale, inverted=inverted, font_data=font_data, height=height
        )

    def blit(self, buf, x, y, key=-1, palette=None):
        """
        Blit the given buffer at the given location.

        Args:
            buf (FrameBuffer): FrameBuffer to blit
            x (int): x coordinate
            y (int): y coordinate
            key (int): Color key (default: -1)
            palette (list): Palette (default: None)

        Returns:
            (Area): Bounding box of the blitted buffer
        """
        super().blit(buf, x, y, key, palette)
        return Area(x, y, buf.width, buf.height)

    ########### Additional methods

    def arc(self, *args, **kwargs):
        """
        Arc drawing function.  Will draw a single pixel wide arc with a radius r
        centered at x, y from a0 to a1.

        Args:
            x (int): X-coordinate of the arc's center.
            y (int): Y-coordinate of the arc's center.
            r (int): Radius of the arc.
            a0 (float): Starting angle in degrees.
            a1 (float): Ending angle in degrees.
            c (int): color.

        Returns:
            (Area): The bounding box of the arc.
        """
        return _shapes.arc(self, *args, **kwargs)

    def blit_rect(self, buf, x, y, w, h):
        """
        Blit a rectangular area from a buffer to the canvas.  Uses the canvas's blit_rect method if available,
        otherwise writes directly to the buffer.

        Args:
            buf (memoryview): Buffer to blit. Must already be byte-swapped if necessary.
            x (int): X-coordinate to blit to.
            y (int): Y-coordinate to blit to.
            w (int): Width of the area to blit.
            h (int): Height of the area to blit.

        Returns:
            (Area): The bounding box of the blitted area.
        """
        BPP = 2

        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            raise ValueError("The provided x, y, w, h values are out of range")

        if len(buf) != w * h * BPP:
            print(f"len(buf)={len(buf)} w={w} h={h} self.color_depth={self.color_depth}")
            raise ValueError("The source buffer is not the correct size")

        for row in range(h):
            source_begin = row * w * BPP
            source_end = source_begin + w * BPP
            dest_begin = ((y + row) * self.width + x) * BPP
            dest_end = dest_begin + w * BPP
            self.buffer[dest_begin:dest_end] = buf[source_begin:source_end]
        return Area(x, y, w, h)

    def blit_transparent(self, *args, **kwargs):
        """
        Blit a buffer with transparency.

        Args:
            buf (memoryview): Buffer to blit.
            x (int): X-coordinate to blit to.
            y (int): Y-coordinate to blit to.
            w (int): Width of the area to blit.
            h (int): Height of the area to blit.
            key (int): Key value for transparency.

        Returns:
            (Area): The bounding box of the blitted area.
        """
        return _shapes.blit_transparent(self, *args, **kwargs)

    def circle(self, *args, **kwargs):
        """
        Circle drawing function.  Will draw a single pixel wide circle
        centered at x0, y0 and the specified r.

        Args:
            x0 (int): Center x coordinate
            y0 (int): Center y coordinate
            r (int): Radius
            c (int): Color
            f (bool): Fill the circle (default: False)

        Returns:
            (Area): The bounding box of the circle.
        """
        return _shapes.circle(self, *args, **kwargs)

    def gradient_rect(self, *args, **kwargs):
        """
        Fill a rectangle with a gradient.

        Args:
            x (int): X-coordinate of the top-left corner of the rectangle.
            y (int): Y-coordinate of the top-left corner of the rectangle.
            w (int): Width of the rectangle.
            h (int): Height of the rectangle.
            c1 (int): 565 encoded color for the top or left edge.
            c2 (int): 565 encoded color for the bottom or right edge.  If None or the same as c1,
                        fill_rect will be called instead.
            vertical (bool): If True, the gradient will be vertical.  If False, the gradient will be horizontal.

        Returns:
            (Area): The bounding box of the filled area.
        """
        return _shapes.gradient_rect(self, *args, **kwargs)

    def polygon(self, *args, **kwargs):
        """
        Draw a polygon on the canvas.

        Args:
            points (list): List of points to draw.
            x (int): X-coordinate of the polygon's position.
            y (int): Y-coordinate of the polygon's position.
            color (int): color.
            angle (float): Rotation angle in radians (default: 0).
            center_x (int): X-coordinate of the rotation center (default: 0).
            center_y (int): Y-coordinate of the rotation center (default: 0).

        Raises:
            ValueError: If the polygon has less than 3 points.

        Returns:
            (Area): The bounding box of the polygon.
        """
        return _shapes.polygon(self, *args, **kwargs)

    def round_rect(self, *args, **kwargs):
        """
        Rounded rectangle drawing function.  Will draw a single pixel wide rounded rectangle starting at
        x0, y0 and extending w, h pixels with the specified radius.

        Args:
            x0 (int): X-coordinate of the top-left corner of the rectangle.
            y0 (int): Y-coordinate of the top-left corner of the rectangle.
            w (int): Width of the rectangle.
            h (int): Height of the rectangle.
            r (int): Radius of the corners.
            c (int): color.
            f (bool): Fill the rectangle (default: False).

        Returns:
            (Area): The bounding box of the rectangle.
        """
        return _shapes.round_rect(self, *args, **kwargs)

    def triangle(self, *args, **kwargs):
        """
        Triangle drawing function.  Draws a single pixel wide triangle with vertices at
        (x0, y0), (x1, y1), and (x2, y2).

        Args:
            x0 (int): X-coordinate of the first vertex.
            y0 (int): Y-coordinate of the first vertex.
            x1 (int): X-coordinate of the second vertex.
            y1 (int): Y-coordinate of the second vertex.
            x2 (int): X-coordinate of the third vertex.
            y2 (int): Y-coordinate of the third vertex.
            c (int): color.
            f (bool): Fill the triangle (default: False).

        Returns:
            (Area): The bounding box of the triangle.
        """
        return _shapes.triangle(self, *args, **kwargs)

    def text8(self, *args, **kwargs):
        """
        Place text on the canvas with an 8 pixel high font.
        Breaks on \n to next line.  Does not break on line going off canvas.

        Args:
            canvas (Canvas): The DisplayDriver, FrameBuffer, or other canvas-like object to draw on.
            s (str): The text to draw.
            x (int): The x position to start drawing the text.
            y (int): The y position to start drawing the text.
            c (int): The color to draw the text in.  Default is 1.
            scale (int): The scale factor to draw the text at.  Default is 1.
            inverted (bool): If True, draw the text inverted.  Default is False.
            font_data (str): The path to the font file to use.  Default is None.

        Returns:
            Area: The area that was drawn to.
        """
        return _font.text8(self, *args, **kwargs)

    def text14(self, *args, **kwargs):
        """
        Place text on the canvas with a 14 pixel high font.
        Breaks on \n to next line.  Does not break on line going off canvas.

        Args:
            canvas (Canvas): The DisplayDriver, FrameBuffer, or other canvas-like object to draw on.
            s (str): The text to draw.
            x (int): The x position to start drawing the text.
            y (int): The y position to start drawing the text.
            c (int): The color to draw the text in.  Default is 1.
            scale (int): The scale factor to draw the text at.  Default is 1.
            inverted (bool): If True, draw the text inverted.  Default is False.
            font_data (str): The path to the font file to use.  Default is None.

        Returns:
            Area: The area that was drawn to.
        """
        return _font.text14(self, *args, **kwargs)

    def text16(self, *args, **kwargs):
        """
        Place text on the canvas with a 16 pixel high font.
        Breaks on \n to next line.  Does not break on line going off canvas.

        Args:
            canvas (Canvas): The DisplayDriver, FrameBuffer, or other canvas-like object to draw on.
            s (str): The text to draw.
            x (int): The x position to start drawing the text.
            y (int): The y position to start drawing the text.
            c (int): The color to draw the text in.  Default is 1.
            scale (int): The scale factor to draw the text at.  Default is 1.
            inverted (bool): If True, draw the text inverted.  Default is False.
            font_data (str): The path to the font file to use.  Default is None.

        Returns:
            Area: The area that was drawn to.
        """
        return _font.text16(self, *args, **kwargs)

    def save(self, filename=None):
        """
        Save the framebuffer to a file.  The file extension must match the format, otherwise
        the extension will be appended to the filename.

        Saves 1-bit formats as PBM, 2-bit formats as PGM with max value 3, 4-bit formats as PGM with max value 15,
        8-bit formats as PGM with max value 255, and 16-bit formats as BMP.

        Args:
            filename (str): Filename to save to
        """
        if filename is None:
            filename = "screenshot"
        file_ext = filename.split(".")[-1]
        if self.format == MONO_HLSB:
            if file_ext != "pbm":
                filename += ".pbm"
            with open(filename, "wb") as f:
                f.write(b"P4\n")
                f.write(f"{self.width} {self.height}\n".encode())
                f.write(self.buffer)
        elif self.format == GS2_HMSB:
            if file_ext != "pgm":
                filename += ".pgm"
            with open(filename, "wb") as f:
                f.write(b"P5\n")
                f.write(f"{self.width} {self.height}\n".encode())
                f.write(b"3\n")
                f.write(self.buffer)
        elif self.format == GS4_HMSB:
            if file_ext != "pgm":
                filename += ".pgm"
            with open(filename, "wb") as f:
                f.write(b"P5\n")
                f.write(f"{self.width} {self.height}\n".encode())
                f.write(b"15\n")
                f.write(self.buffer)
        elif self.format == GS8:
            if file_ext != "pgm":
                filename += ".pgm"
            with open(filename, "wb") as f:
                f.write(b"P5\n")
                f.write(f"{self.width} {self.height}\n".encode())
                f.write(b"255\n")
                f.write(self.buffer)
        elif self.format == RGB565:
            if file_ext != "bmp":
                filename += ".bmp"
            with open(filename, "wb") as f:
                f.write(b"BM")  # Offset 0: Signature
                f.write((54 + len(self.buffer)).to_bytes(4, "little"))  # Offset 2: File size
                f.write(b"\x00\x00\x00\x00")  # Offset 6: Unused
                f.write(b"\x36\x00\x00\x00")  # Offset 10: Offset to image data
                f.write(b"\x28\x00\x00\x00")  # Offset 14: DIB header size
                f.write(self.width.to_bytes(4, "little"))  # Offset 18: Width
                f.write(self.height.to_bytes(4, "little"))  # Offset 22: Height
                f.write(b"\x01\x00")  # Offset 26: Planes
                f.write(b"\x10\x00")  # Offset 28: Bits per pixel
                f.write(b"\x00\x00\x00\x00")  # Offset 30: Compression
                f.write(len(self.buffer).to_bytes(4, "little"))  # Offset 34: Image size
                f.write(
                    b"\x00\x00\x00\x00\x00\x00\x00\x00"
                )  # Offset 38: Horizontal and vertical resolution
                f.write(b"\x00\x00\x00\x00")  # Offset 46: Colors in palette
                f.write(b"\x00\x00\x00\x00")  # Offset 50: Important colors
                # The order of the lines is reversed.  We need to reverse them back.
                for i in range(self.height):
                    f.write(
                        self.buffer[
                            (self.height - i - 1) * self.width * 2 : (self.height - i)
                            * self.width
                            * 2
                        ]
                    )
        else:
            raise ValueError(f"Save method not implemented for format {self.format}")

    @staticmethod
    def from_file(filename):
        """
        Load a framebuffer from a file.

        Args:
            filename (str): Filename to load from
        """
        # Read the first two bytes to determine the file type
        f = open(filename, "rb")
        header = f.read(2)
        f.close()

        if header == b"P4":
            return _files.pbm_to_framebuffer(filename)
        elif header == b"P5":
            return _files.pgm_to_framebuffer(filename)
        elif header == b"BM":
            return _files.bmp_to_framebuffer(filename)
        else:
            raise ValueError(f"Unsupported file type {header}")
