"""
framebuf.py - for compatibility with the MicroPython framebuf module
in CPython and CircuitPython.
"""

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
