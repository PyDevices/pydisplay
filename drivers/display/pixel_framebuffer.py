# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
Helper to construct a CircuitPython PixelFramebuffer for use with PixelDisplay.

On MicroPython, a compatible implementation is not yet available — see
docs/hardware/display-interfaces.md.
"""


def create_pixel_framebuffer(pixels, width, height, *, byteorder="RGB", rotation=0, top=0):
    """
    Create an ``adafruit_pixel_framebuf.PixelFramebuffer`` on CircuitPython.

    Args:
        pixels: ``neopixel.NeoPixel``, ``adafruit_dotstar.DotStar``, or compatible.
        width (int): Grid width in pixels.
        height (int): Grid height in pixels.
        byteorder (str): ``"RGB"`` or ``"GRB"`` etc., passed to PixelFramebuffer.
        rotation (int): Rotation in degrees (0, 90, 180, 270).
        top (int): First pixel index in the strip (for offset wiring).

    Returns:
        PixelFramebuffer instance.
    """
    from adafruit_pixel_framebuf import PixelFramebuffer

    return PixelFramebuffer(
        pixels,
        width,
        height,
        byteorder=byteorder,
        rotation=rotation,
        top=top,
    )
