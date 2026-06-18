"""
`graphics`
====================================================
Graphics library extending MicroPython's framebuf module.
"""

from ._area import Area
from ._draw import Draw
from ._files import bmp_to_framebuffer, pbm_to_framebuffer, pgm_to_framebuffer
from ._font import Font, text, text8, text14, text16
from ._framebuf_plus import (
    GS2_HMSB,
    GS4_HMSB,
    GS8,
    MONO_HLSB,
    MONO_HMSB,
    MONO_VLSB,
    RGB565,
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
    "circle",
    "ellipse",
    "fill",
    "fill_rect",
    "gradient_rect",
    "hline",
    "line",
    "pbm_to_framebuffer",
    "pgm_to_framebuffer",
    "pixel",
    "poly",
    "polygon",
    "rect",
    "round_rect",
    "text",
    "text8",
    "text14",
    "text16",
    "triangle",
    "vline",
]
