"""Qualia S3 RGB-666 with TL040HDS20 4.0" 720x720 Square Display"""
# Similar configs may be available for RGBMatrix, is31fl3741 and picodvi

import adafruit_focaltouch
import board
import busio
from displayio import release_displays
import dotclockframebuffer
from framebufferio import FramebufferDisplay

from displaysys.fbdisplay import FBDisplay
import eventsys

# This first part is particular to CircuitPython-based framebuffer-based displays

tft_pins = dict(board.TFT_PINS)

tft_timings = {
    "frequency": 16000000,
    "width": 720,
    "height": 720,
    "hsync_pulse_width": 2,
    "hsync_front_porch": 46,
    "hsync_back_porch": 44,
    "vsync_pulse_width": 2,
    "vsync_front_porch": 16,
    "vsync_back_porch": 18,
    "hsync_idle_low": False,
    "vsync_idle_low": False,
    "de_idle_high": False,
    "pclk_active_high": False,
    "pclk_idle_high": False,
}

init_sequence_tl040hds20 = bytes()

board.I2C().deinit()
i2c = busio.I2C(board.SCL, board.SDA)
tft_io_expander = dict(board.TFT_IO_EXPANDER)
# tft_io_expander['i2c_address'] = 0x38 # uncomment for rev B
dotclockframebuffer.ioexpander_send_init_sequence(i2c, init_sequence_tl040hds20, **tft_io_expander)

release_displays()
fb = dotclockframebuffer.DotClockFramebuffer(**tft_pins, **tft_timings)
display = FramebufferDisplay(fb, auto_refresh=True)
display.root_group = None


# Typical board_config.py setup from here on out

display_drv = FBDisplay(fb)

touch_drv = adafruit_focaltouch.Adafruit_FocalTouch(i2c, address=0x48)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = (0, 0, 0, 0)

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
