"""M5Stack Tab5 — CircuitPython (ESP32-P4 + MIPI DSI)

Uses CircuitPython ``mipidsi`` (board DSI pins) — not displayif.

Early Tab5 units: ILI9881C + GT911 @ 0x14. Newer units: ST7123 integrated TDDI
(use latest CP build from circuitpython.org / S3 alpha bucket).

Product: https://circuitpython.org/board/m5stack_tab5/
"""

import board
import busio
import displayio
import gt911
import mipidsi
import time

from displaysys.fbdisplay import FBDisplay
from tab5_ili9881c_init import TAB5_ILI9881C_INIT
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

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
