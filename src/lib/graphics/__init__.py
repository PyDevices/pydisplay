"""
graphics — cross-platform 2D drawing for *Python.

Extends MicroPython's ``framebuf`` with shape helpers, fonts, image loaders, and
``Area`` bounding boxes for partial updates.  On CPython and CircuitPython the
built-in pure-Python ``_framebuf`` fallback is used automatically.

Quick start::

    import graphics

    fb = graphics.FrameBuffer(bytearray(16 * 16 * 2), 16, 16, graphics.RGB565)
    fb.fill(0)
    area = fb.fill_rect(1, 1, 6, 6, 0xFFFF)
    graphics.text8(fb, "Hi", 0, 0, 0xFFFF)

    print(graphics.capabilities())
"""

from ._area import Area
from ._bmp565 import BMP565
from ._capabilities import capabilities, framebuf_backend
from ._draw import Draw
from ._files import (
    bmp_to_framebuffer,
    load_image,
    pbm_to_framebuffer,
    pgm_to_framebuffer,
    save_image,
)
from ._font import Font, text, text8, text14, text16
from ._framebuf_plus import (
    GS2_HMSB,
    GS4_HMSB,
    GS8,
    MONO_HLSB,
    MONO_HMSB,
    MONO_VLSB,
    RGB565,
    RGB888,
    FrameBuffer,
)
from ._shapes import (
    arc,
    blit,
    blit_rect,
    blit_transparent,
    circle,
    ellipse,
    fill,
    fill_rect,
    gradient_rect,
    hline,
    line,
    pixel,
    poly,
    polygon,
    rect,
    round_rect,
    triangle,
    vline,
)

__all__ = [
    "BMP565",
    "GS2_HMSB",
    "GS4_HMSB",
    "GS8",
    "MONO_HLSB",
    "MONO_HMSB",
    "MONO_VLSB",
    "RGB565",
    "Area",
    "Draw",
    "Font",
    "FrameBuffer",
    "arc",
    "blit",
    "blit_rect",
    "blit_transparent",
    "bmp_to_framebuffer",
    "capabilities",
    "circle",
    "ellipse",
    "fill",
    "fill_rect",
    "framebuf_backend",
    "gradient_rect",
    "hline",
    "line",
    "load_image",
    "pbm_to_framebuffer",
    "pgm_to_framebuffer",
    "pixel",
    "poly",
    "polygon",
    "rect",
    "round_rect",
    "save_image",
    "text",
    "text8",
    "text14",
    "text16",
    "triangle",
    "vline",
]
