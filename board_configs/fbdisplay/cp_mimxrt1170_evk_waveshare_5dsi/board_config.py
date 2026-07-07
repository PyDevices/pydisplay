"""NXP MIMXRT1170-EVK + Waveshare 50H-800480-IPS DSI (800×480) on J84 — CircuitPython

Board: https://circuitpython.org/board/nxp_mimxrt1170_evk/
Panel: https://www.waveshare.com/wiki/50H-800480-IPS#Interface_Definition
Waveshare 50H-800480-IPS on J84 (15-pin RPi-style FFC) + 5 V on J85.

Touch (50H-800480-IPS-CT only): Goodix GT911 on I2C via J84 FFC pins 11–12
(``board.SCL`` / ``board.SDA``).  Reset / interrupt on ``board.D9`` / ``board.D6``.
Non-touch IPS panels omit the controller; display-only use still works.
"""

import board
import busio
import digitalio
import displayio
import gt911
import mipidsi

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

# CircuitPython native mipidsi (not displayif).
PANEL_INIT_SEQUENCE = b""
bus = mipidsi.Bus(frequency=1_000_000_000, num_lanes=2)

fb = mipidsi.Display(
    bus,
    init_sequence=PANEL_INIT_SEQUENCE,
    width=800,
    height=480,
    color_depth=16,
    pixel_clock_frequency=25_979_400,
    hsync_pulse_width=2,
    hsync_front_porch=1,
    hsync_back_porch=46,
    vsync_pulse_width=2,
    vsync_front_porch=7,
    vsync_back_porch=21,
)

display_drv = FBDisplay(fb)

i2c = busio.I2C(board.SCL, board.SDA)
touch_rst = digitalio.DigitalInOut(board.D9)
touch_rst.direction = digitalio.Direction.OUTPUT
touch_drv = gt911.GT911(i2c, i2c_address=0x5D, rst_pin=touch_rst)


def touch_read_func():
    touches = touch_drv.touches
    if touches:
        return touches[0][0], touches[0][1]
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
