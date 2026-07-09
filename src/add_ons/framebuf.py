"""
framebuf.py - for compatibility with the MicroPython framebuf module
in CPython and CircuitPython.
"""

try:
    import graphics as _g

    FrameBuffer = _g.FrameBuffer
    GS2_HMSB = _g.GS2_HMSB
    GS4_HMSB = _g.GS4_HMSB
    GS8 = _g.GS8
    MONO_HLSB = _g.MONO_HLSB
    MONO_HMSB = _g.MONO_HMSB
    MONO_VLSB = _g.MONO_VLSB
    RGB565 = _g.RGB565
except (ImportError, AttributeError):
    from graphics._framebuf import (
        GS2_HMSB,
        GS4_HMSB,
        GS8,
        MONO_HLSB,
        MONO_HMSB,
        MONO_VLSB,
        RGB565,
        FrameBuffer,
    )

__all__ = [
    "GS2_HMSB",
    "GS4_HMSB",
    "GS8",
    "MONO_HLSB",
    "MONO_HMSB",
    "MONO_VLSB",
    "RGB565",
    "FrameBuffer",
]
