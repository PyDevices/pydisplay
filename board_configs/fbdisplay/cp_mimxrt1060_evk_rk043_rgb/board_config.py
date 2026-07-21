"""NXP MIMXRT1060-EVK + RK043FN66HS-CTG 4.3" parallel RGB — CircuitPython"""

import time

import board
import busio
import digitalio
import displayio
import dotclockframebuffer
import gt911

from displaysys.fbdisplay import FBDisplay
import eventsys

board.LCD_BACKLIGHT.value = True

board.LCD_RST.value = False
time.sleep(0.01)
board.LCD_RST.value = True
time.sleep(0.12)

displayio.release_displays()

fb = dotclockframebuffer.DotClockFramebuffer(
    de=board.LCD_ENABLE,
    vsync=board.LCD_VSYNC,
    hsync=board.LCD_HSYNC,
    dclk=board.LCD_CLK,
    data=(
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
    ),
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

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
