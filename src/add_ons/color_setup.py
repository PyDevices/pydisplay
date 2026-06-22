"""
color_setup.py - color setup for DisplayBuffer with displaysys
Usage:
    from color_setup import ssd
    <your code here>
"""

from board_config import display_drv
from displaybuf import DisplayBuffer as SSD

from multimer import REQUIRES_RUN_QUEUED

# SSD.RGB565 is supported by all implementations, so set it as the default format
# Micropython also supports SSD.GS4_HMSB and SSD.GS8
# format = SSD.GS4_HMSB  # 4-bit (16 item) lookup table of 16-bit RGB565 colors; w*h/2 buffer
# format = SSD.GS8  # 256 8-bit RGB332 colors; w*h buffer
format = SSD.RGB565  # all 65,536 16-bit RGB565 colors; w*h*2 buffer

ssd = SSD(display_drv, format)

# DisplayBuffer.show() blits to the driver texture; on queued/SDL backends
# display_drv.show() is also required to present the frame.  MCU BusDisplay
# show() is a no-op, so this is safe everywhere run_queued is required.
if REQUIRES_RUN_QUEUED:
    _orig_show = ssd.show

    def show(area=None):
        _orig_show(area)
        display_drv.show()

    ssd.show = show
