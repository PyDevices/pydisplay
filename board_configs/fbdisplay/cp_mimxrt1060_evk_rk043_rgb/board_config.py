"""NXP MIMXRT1060-EVK + RK043FN66HS-CTG 4.3\" parallel RGB — CircuitPython

Touch: Goodix GT911 on shield I2C (``board.SCL`` / ``board.SDA``), reset on
``board.LCD_RST``, interrupt on ``board.LCD_TOUCH_INT``.
"""

import board
import busio
import displayio
import digitalio
import gt911
import time

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

try:
    from rgbframebuffer import RGBFrameBuffer
except ImportError as exc:
    raise NotImplementedError(
        "Parallel RGB scanout requires displayif rgbframebuffer cmod (mimxrt eLCDIF)"
    ) from exc

board.LCD_BACKLIGHT.value = True

board.LCD_RST.value = False
time.sleep(0.01)
board.LCD_RST.value = True
time.sleep(0.12)

data_pins = (
    board.LCD_D0,
    board.LCD_D1,
    board.LCD_D2,
    board.LCD_D3,
    board.LCD_D4,
    board.LCD_D5,
    board.LCD_D6,
    board.LCD_D7,
    board.LCD_D8,
    board.LCD_D9,
    board.LCD_D10,
    board.LCD_D11,
    board.LCD_D12,
    board.LCD_D13,
    board.LCD_D14,
    board.LCD_D15,
)

fb = RGBFrameBuffer(
    de=board.LCD_ENABLE,
    vsync=board.LCD_VSYNC,
    hsync=board.LCD_HSYNC,
    dclk=board.LCD_CLK,
    data=data_pins,
    frequency=9_000_000,
    width=480,
    height=272,
    hsync_pulse_width=41,
    hsync_front_porch=4,
    hsync_back_porch=8,
    vsync_pulse_width=10,
    vsync_front_porch=4,
    vsync_back_porch=2,
    hsync_idle_low=True,
    vsync_idle_low=True,
    de_idle_high=False,
    pclk_active_high=False,
    pclk_idle_high=False,
)

display_drv = FBDisplay(fb)

i2c = busio.I2C(board.SCL, board.SDA)
touch_rst = digitalio.DigitalInOut(board.LCD_RST)
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
