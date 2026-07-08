"""M5Stack Tab5 — CircuitPython (ESP32-P4 + MIPI DSI)

Uses CircuitPython ``mipidsi`` (board DSI pins) — not displayif.

Early Tab5 units: ILI9881C + GT911 @ 0x14. Newer units: ST7123 integrated TDDI
(use latest CP build from circuitpython.org / S3 alpha bucket).

Product: https://circuitpython.org/board/m5stack_tab5/
"""

import time

import board
import busio
import displayio
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
    height=1280,
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

display = displayio.FramebufferDisplay(fb, auto_refresh=True)
display.root_group = None

i2c = busio.I2C(board.SCL, board.SDA)
touch_drv = gt911.GT911(i2c, i2c_address=0x14)


def touch_read_func():
    touches = touch_drv.touches
    if touches:
        return touches[0][0], touches[0][1]
    return None


display_drv = FBDisplay(fb)

touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
