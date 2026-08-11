# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.pixeldisplay — addressable LED grids (NeoPixel, DotStar, etc.).

MicroPython: ``PixelFramebuffer`` (RGB888 grid + strip map) and ``PixelDisplay``
live here.  CircuitPython board configs use
``adafruit_pixel_framebuf.PixelFramebuffer`` with pydisplay ``PixelDisplay``.
"""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


from displaysys import DisplayDriver, color_rgb


def _color888_from_565(c):
    r, g, b = color_rgb(c)
    return (r << 16) | (g << 8) | b


def _rgb888_bytes(c):
    return bytes(((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF))


HORIZONTAL = const(1)
VERTICAL = const(2)


def _horizontal_strip_gridmap(width, alternating=True):
    def mapper(x, y):
        if alternating and y % 2:
            return y * width + (width - 1 - x)
        return y * width + x

    return mapper


def _vertical_strip_gridmap(height, alternating=True):
    def mapper(x, y):
        if alternating and x % 2:
            return x * height + (height - 1 - y)
        return x * height + y

    return mapper


def _reverse_x_mapper(width, mapper):
    max_x = width - 1

    def x_mapper(x, y):
        return mapper(max_x - x, y)

    return x_mapper


def _reverse_y_mapper(height, mapper):
    max_y = height - 1

    def y_mapper(x, y):
        return mapper(x, max_y - y)

    return y_mapper


def _build_grid_mapper(
    width,
    height,
    *,
    orientation=HORIZONTAL,
    alternating=True,
    reverse_x=False,
    reverse_y=False,
    top=0,
    bottom=0,
):
    if orientation == HORIZONTAL:
        mapper = _horizontal_strip_gridmap(width, alternating)
    else:
        mapper = _vertical_strip_gridmap(height, alternating)

    if reverse_x:
        mapper = _reverse_x_mapper(width, mapper)
    if reverse_y:
        mapper = _reverse_y_mapper(height, mapper)

    x_start = 0
    x_end = width
    y_start = 0
    y_end = height
    if top:
        x_start, y_start = top
    if bottom:
        x_end, y_end = bottom

    grid_width = x_end - x_start
    grid_height = y_end - y_start
    indices = []
    for _y in range(grid_height):
        for _x in range(grid_width):
            indices.append(mapper(_x + x_start, _y + y_start))
    return grid_width, grid_height, indices


class PixelFramebuffer:
    """
    NeoPixel / DotStar grid framebuffer for MicroPython.

    Same constructor signature as ``adafruit_pixel_framebuf.PixelFramebuffer``.
    Flush changed pixels to the strip with ``display()``.
    """

    def __init__(
        self,
        pixels,
        width,
        height,
        orientation=HORIZONTAL,
        alternating=True,
        reverse_x=False,
        reverse_y=False,
        top=0,
        bottom=0,
        rotation=0,
    ):
        """Build a grid framebuffer mapped onto an addressable LED strip.

        Args:
            pixels: NeoPixel / DotStar-like object with ``__setitem__`` and ``show()``.
            width: Logical grid width.
            height: Logical grid height.
            orientation: :data:`HORIZONTAL` or :data:`VERTICAL` strip layout.
            alternating: Zigzag rows/columns when True.
            reverse_x: Mirror X before mapping.
            reverse_y: Mirror Y before mapping.
            top: Optional ``(x, y)`` origin of the active sub-grid.
            bottom: Optional ``(x, y)`` exclusive end of the active sub-grid.
            rotation: Stored rotation attribute (degrees).
        """
        self._pixels = pixels
        grid_width, grid_height, self._indices = _build_grid_mapper(
            width,
            height,
            orientation=orientation,
            alternating=alternating,
            reverse_x=reverse_x,
            reverse_y=reverse_y,
            top=top,
            bottom=bottom,
        )
        self._width = grid_width
        self._height = grid_height
        nbytes = grid_width * grid_height * 3
        self._buffer = bytearray(nbytes)
        self._double_buffer = bytearray(nbytes)
        self.rotation = rotation

    @property
    def width(self):
        """Logical grid width in pixels."""
        return self._width

    @property
    def height(self):
        """Logical grid height in pixels."""
        return self._height

    @property
    def stride(self):
        """Pixels per row in the logical framebuffer."""
        return self._width

    def fill_rect(self, x, y, w, h, c):
        """Fill a rectangle with an RGB888 packed color ``0xRRGGBB``."""
        rgb = _rgb888_bytes(c)
        stride = self._width
        if x == 0 and w == stride:
            rowbytes = rgb * w
            for _y in range(y, y + h):
                begin = _y * stride * 3
                self._buffer[begin : begin + len(rowbytes)] = rowbytes
            return (x, y, w, h)
        for _y in range(y, y + h):
            row = _y * stride
            for _x in range(x, x + w):
                index = (row + _x) * 3
                self._buffer[index : index + 3] = rgb
        return (x, y, w, h)

    def pixel(self, x, y, c=None):
        """Get or set one RGB888 packed pixel ``0xRRGGBB``."""
        index = (y * self._width + x) * 3
        if c is None:
            r, g, b = self._buffer[index : index + 3]
            return (r << 16) | (g << 8) | b
        self._buffer[index : index + 3] = _rgb888_bytes(c)

    def blit(self):
        """Not implemented — use :meth:`display` to flush the strip."""
        raise NotImplementedError

    def display(self) -> None:
        """Copy changed pixels to the LED strip and show."""
        stride = self.stride
        for _y in range(self._height):
            for _x in range(self._width):
                index = (_y * stride + _x) * 3
                if self._buffer[index : index + 3] != self._double_buffer[index : index + 3]:
                    grid_index = _y * self._width + _x
                    strip_index = self._indices[grid_index]
                    self._pixels[strip_index] = tuple(self._buffer[index : index + 3])
                    self._double_buffer[index : index + 3] = self._buffer[index : index + 3]
        self._pixels.show()


class PixelDisplay(DisplayDriver):
    """
    DisplayDriver for addressable-LED matrix layouts.

    Exposes the usual RGB565 ``DisplayDriver`` API (``color_depth=16``).  The
    inner ``PixelFramebuffer`` stores RGB888 for the LED strip; conversion uses
    ``color_rgb``.

    Args:
        pixel_buffer: ``PixelFramebuffer`` (or Adafruit equivalent on CircuitPython).
    """

    def __init__(self, pixel_buffer, *, quiet=False):
        self._raw_buffer = pixel_buffer
        self._width = pixel_buffer.width
        self._height = pixel_buffer.height
        self._rotation = getattr(pixel_buffer, "rotation", 0)
        self.color_depth = 16
        self._requires_byteswap = False
        super().__init__(quiet=quiet)

    def init(self) -> None:
        """No-op init hook (LED strip is already configured)."""

    def fill_rect(self, x, y, w, h, c):
        """Fill a rectangle with an RGB565 color (converted to RGB888).

        Args:
            x: Left edge.
            y: Top edge.
            w: Width.
            h: Height.
            c: RGB565 color.

        Returns:
            Result of the inner framebuffer ``fill_rect``.
        """
        return self._raw_buffer.fill_rect(x, y, w, h, _color888_from_565(c))

    def blit_rect(self, buf, x, y, w, h):
        """Blit RGB565 bytes into the LED framebuffer.

        Args:
            buf: Source buffer of ``w * h * 2`` bytes.
            x: Destination left edge.
            y: Destination top edge.
            w: Width in pixels.
            h: Height in pixels.

        Returns:
            tuple: ``(x, y, w, h)``.

        Raises:
            ValueError: When ``buf`` length does not match dimensions.
        """
        bpp = self.color_depth // 8
        expected = w * h * bpp
        if len(buf) != expected:
            raise ValueError(
                f"The source buffer is not the correct size (got {len(buf)} bytes, expected {expected})"
            )
        inner = self._raw_buffer
        for row in range(h):
            row_base = row * w * bpp
            for col in range(w):
                off = row_base + col * bpp
                inner.pixel(x + col, y + row, _color888_from_565(buf[off : off + bpp]))
        return (x, y, w, h)

    def pixel(self, x, y, c):
        """Set a single RGB565 pixel (converted to RGB888).

        Args:
            x: X coordinate.
            y: Y coordinate.
            c: RGB565 color.

        Returns:
            Result of the inner framebuffer ``pixel``.
        """
        return self._raw_buffer.pixel(x, y, _color888_from_565(c))

    def show(self, _timer=None) -> None:
        """Flush dirty pixels to the LED strip via ``pixel_buffer.display()``."""
        self._raw_buffer.display()
