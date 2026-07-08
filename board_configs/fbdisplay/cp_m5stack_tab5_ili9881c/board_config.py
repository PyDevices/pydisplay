"""M5Stack Tab5 (ILI9881C + GT911) — CircuitPython"""

import board
import busio
import displayio
import framebufferio
import gt911
import mipidsi
from tab5_ili9881c_init import TAB5_ILI9881C_INIT

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

bus = mipidsi.Bus(frequency=730_000_000, num_lanes=2)

fb = mipidsi.Display(
    bus,
    init_sequence=TAB5_ILI9881C_INIT,
    width=720,
    height=1_280,
    color_depth=16,
    pixel_clock_frequency=60_000_000,
    hsync_pulse_width=40,
    hsync_front_porch=40,
    hsync_back_porch=140,
    vsync_pulse_width=4,
    vsync_front_porch=20,
    vsync_back_porch=20,
    backlight_pin=board.LCD_BL,
    backlight_on_high=True,
)

display = framebufferio.FramebufferDisplay(fb, auto_refresh=True)
display.root_group = None

display_drv = FBDisplay(fb)

i2c = busio.I2C(board.SCL, board.SDA)
touch_drv = gt911.GT911(i2c, i2c_address=0x14)


def touch_read_func():
    touches = touch_drv.touches
    if touches:
        return touches[0][0], touches[0][1]
    return None


touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
