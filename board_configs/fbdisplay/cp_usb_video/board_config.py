"""
usb_video - Allows streaming to a host computer via USB emulating a webcam

This is a CircuitPython only capability, and currently is only supported on RP2040 boards.
See:
    https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html
    https://github.com/adafruit/circuitpython/pull/8831

Currently, it shows up on Windows as an unsupported USB Composite Device, so it isn't working.
It is working on Unix, including ChromeOS.  To see how to enable external cameras on ChromeOS:
    https://support.google.com/chromebook/thread/187930465/how-do-i-use-my-usb-webcam?hl=en

The `auto_refresh` setting is not working, so `display_drv.show()` must be called after drawing
to the buffer.

NOTE:  You must put the following 2 lines in your boot.py.  Currently, the width and height
are set to 160 and 120 regardless of what you enter.

    from usb_video import enable_framebuffer
    enable_framebuffer(160, 120)
"""

from displayio import release_displays
from framebufferio import FramebufferDisplay
from usb_video import USBFramebuffer

from displaysys.fbdisplay import FBDisplay

release_displays()
display = FramebufferDisplay(USBFramebuffer(), auto_refresh=True)
fb = display.framebuffer
display.root_group = None

display_drv = FBDisplay(fb, reverse_bytes_in_word=True)
display_drv.fill(0x000F)
display_drv.show()

runtime = None
