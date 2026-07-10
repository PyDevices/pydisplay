from . import _files, _font, _shapes
from ._area import Area
from ._blit_hooks import clip_blit_bounds

try:
    # Local submodule: present in TestPyPI wheels and after tools/sync_framebuf.py runs.
    from .framebuf import (
        GS2_HMSB,
        GS4_HMSB,
        GS8,
        MONO_HLSB,
        MONO_HMSB,
        MONO_VLSB,
        RGB565,
    )
    from .framebuf import FrameBuffer as _FrameBuffer
except ImportError:
    # graphics/framebuf.py is a generated packaging artifact (gitignored) not present
    # in all deploy paths (PyScript, mip-install from GitHub, bare CP/MP without wheel).
    # Fall back to the bare framebuf module: native C on MicroPython hardware,
    # or add_ons/framebuf.py when add_ons/ is on sys.path (PyScript, CircuitPython, etc.).
    from framebuf import (  # type: ignore[no-redef]
        GS2_HMSB,
        GS4_HMSB,
        GS8,
        MONO_HLSB,
        MONO_HMSB,
        MONO_VLSB,
        RGB565,
    )
    from framebuf import FrameBuffer as _FrameBuffer  # type: ignore[no-redef]

# pydisplay extension — not in MicroPython framebuf
RGB888 = 7


class _RGB888Format:
    depth = 24

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        index = (y * framebuf._stride + x) * 3
        framebuf._buffer[index : index + 3] = bytes(
            ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)
        )

    @staticmethod
    def get_pixel(framebuf, x, y):
        index = (y * framebuf._stride + x) * 3
        r, g, b = framebuf._buffer[index : index + 3]
        return (r << 16) | (g << 8) | b

    @staticmethod
    def fill(framebuf, color):
        rgb = bytes(((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF))
        for i in range(0, len(framebuf._buffer), 3):
            framebuf._buffer[i : i + 3] = rgb

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        rgb = bytes(((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF))
        stride = framebuf._stride
        for _y in range(y, y + height):
            row = _y * stride
            for _x in range(x, x + width):
                index = (row + _x) * 3
                framebuf._buffer[index : index + 3] = rgb


class FrameBuffer(_FrameBuffer):
    """
    An extension of MicroPython's framebuf.FrameBuffer that adds some useful methods for drawing shapes and text.
    Each method returns a bounding box (x, y, w, h) of the drawn shape to indicate
    the area of the display that was modified.  This can be used to update only the
    modified area of the display.  Exposes attributes not exposed in the base class, such
    as color_depth, width, height, buffer, and format.  Also adds a save method to save
    the framebuffer to a file, and a from_file method to load a framebuffer from a file.

    Inherits from the bundled pure-Python ``.framebuf.FrameBuffer`` (never the
    compiled native ``framebuf`` module, to guarantee identical behavior across
    runtimes). Methods should return an Area object, but the MicroPython
    framebuf module returns None, so the methods inherited from
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
        self._rgb888 = format == RGB888
        # RGB888 is a pydisplay extension; base framebuf never implements it.
        # Initialize the C extmod base as RGB565 so MicroPython does not fall back
        # to make_new with an invalid format.  Pixel ops use _RGB888Format below.
        if self._rgb888:
            super().__init__(buffer, width, height, RGB565)
        else:
            super().__init__(buffer, width, height, format, *args, **kwargs)
        self._width = width
        self._height = height
        self._fb_format = format
        self._buffer = buffer
        if self._rgb888:
            stride = args[0] if args else kwargs.get("stride")
            self._stride = stride if stride is not None else width
            self._color_depth = 24
        elif format in (MONO_VLSB, MONO_HLSB, MONO_HMSB):
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
        if self._rgb888:
            _RGB888Format.fill_rect(self, x, y, w, h, c)
            return Area(x, y, w, h)
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
        if self._rgb888:
            if c is None:
                return _RGB888Format.get_pixel(self, x, y)
            _RGB888Format.set_pixel(self, x, y, c)
            return Area(x, y, 1, 1)
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
        if self._rgb888:
            _RGB888Format.fill(self, c)
            return Area(0, 0, self.width, self.height)
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

    def blit(self, source, x, y, key=-1, palette=None):
        """
        Blit the given buffer at the given location.

        Args:
            source (FrameBuffer): FrameBuffer to blit
            x (int): x coordinate
            y (int): y coordinate
            key (int): Color key (default: -1)
            palette (FrameBuffer): Palette (default: None)

        Returns:
            (Area): Bounding box of the blitted buffer
        """
        super().blit(source, x, y, key, palette)
        clipped = clip_blit_bounds(self, source, x, y)
        if clipped is None:
            return None
        x0, y0, w, h, _, _ = clipped
        return Area(x0, y0, w, h)

    ########### Additional methods

    def arc(self, x, y, r, a0, a1, c):
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
        return _shapes.arc(self, x, y, r, a0, a1, c)

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
        return _shapes.blit_rect(self, buf, x, y, w, h)

    def blit_transparent(self, buf, x, y, w, h, key):
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
        return _shapes.blit_transparent(self, buf, x, y, w, h, key)

    def circle(self, x0, y0, r, c, f=False):
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
        return _shapes.circle(self, x0, y0, r, c, f)

    def gradient_rect(self, x, y, w, h, c1, c2=None, vertical=True):
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
        return _shapes.gradient_rect(self, x, y, w, h, c1, c2, vertical)

    def polygon(self, points, x, y, color, angle=0, center_x=0, center_y=0):
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
        return _shapes.polygon(self, points, x, y, color, angle, center_x, center_y)

    def round_rect(self, x0, y0, w, h, r, c, f=False):
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
        return _shapes.round_rect(self, x0, y0, w, h, r, c, f)

    def triangle(self, x0, y0, x1, y1, x2, y2, c, f=False):
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
        return _shapes.triangle(self, x0, y0, x1, y1, x2, y2, c, f)

    def text8(self, s, x, y, c=1, scale=1, inverted=False, font_data=None):
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

        Returns:
            Area: The area that was drawn to.
        """
        return _font.text8(self, s, x, y, c, scale, inverted, font_data)

    def text14(self, s, x, y, c=1, scale=1, inverted=False, font_data=None):
        """
        Place text on the canvas with a 14 pixel high font.
        Breaks on \n to next line.  Does not break on line going off canvas.

        Args:
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
        return _font.text14(self, s, x, y, c, scale, inverted, font_data)

    def text16(self, s, x, y, c=1, scale=1, inverted=False, font_data=None):
        """
        Place text on the canvas with a 16 pixel high font.
        Breaks on \n to next line.  Does not break on line going off canvas.

        Args:
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
        return _font.text16(self, s, x, y, c, scale, inverted, font_data)

    def scroll(self, xstep, ystep):
        """Scroll buffer contents. Returns the full buffer bounds."""
        super().scroll(xstep, ystep)
        return Area(0, 0, self.width, self.height)

    def save(self, filename=None):
        """
        Save the framebuffer to a file.  The file extension must match the format, otherwise
        the extension will be appended to the filename.

        Saves 1-bit formats as PBM, 2-bit formats as PGM with max value 3, 4-bit formats as PGM with max value 15,
        8-bit formats as PGM with max value 255, and 16-bit formats as BMP.

        Args:
            filename (str): Filename to save to
        """
        return _files.save_image(self, filename)

    @staticmethod
    def from_file(filename):
        """
        Load a framebuffer from a file.

        Args:
            filename (str): Filename to load from
        """
        return _files.load_image(filename)
