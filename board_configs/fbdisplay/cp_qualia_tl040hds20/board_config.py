"""Qualia S3 RGB-666 with TL040HDS20 4.0" 720x720 Square Display"""

from adafruit_focaltouch import Adafruit_FocalTouch
import board
import busio
import displayio
import dotclockframebuffer
import framebufferio

from displaysys.fbdisplay import FBDisplay
import eventsys

tft_pins = dict(board.TFT_PINS)

tft_timings = {
    "frequency": 16_000_000,
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
dotclockframebuffer.ioexpander_send_init_sequence(i2c, init_sequence_tl040hds20, **tft_io_expander)
displayio.release_displays()

fb = dotclockframebuffer.DotClockFramebuffer(**tft_pins, **tft_timings)

display = framebufferio.FramebufferDisplay(fb, auto_refresh=True)
display.root_group = None

display_drv = FBDisplay(fb)

i2c = board.I2C()
touch_drv = Adafruit_FocalTouch(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
