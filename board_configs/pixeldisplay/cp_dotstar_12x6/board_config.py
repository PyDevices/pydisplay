"""DotStar 12x6 grid — CircuitPython DotStar grid"""

import adafruit_dotstar
from adafruit_pixel_framebuf import PixelFramebuffer
import board

from displaysys.pixeldisplay import PixelDisplay

pixel_width = 12
pixel_height = 6

pixels = adafruit_dotstar.DotStar(
    board.D13,
    board.D11,
    pixel_width * pixel_height,
    brightness=0.3,
    auto_write=False,
)

_pixel_framebuf = PixelFramebuffer(
    pixels,
    pixel_width,
    pixel_height,
    alternating=False,
)

display_drv = PixelDisplay(_pixel_framebuf)

runtime = None
