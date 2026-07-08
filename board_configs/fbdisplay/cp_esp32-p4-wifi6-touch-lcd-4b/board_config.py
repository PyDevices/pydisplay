"""Waveshare ESP32-P4-WIFI6-Touch-LCD-4B - 720x720 MIPI DSI + GT911 touch

Product: https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-4b.htm
Wiki:    https://www.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-4B

4-inch 720x720 IPS panel (ST7703) on MIPI DSI.  GT911 capacitive touch on I2C.
Pin assignments match the Waveshare ``esp32_p4_wifi6_touch_lcd_4b`` BSP.

Requires CircuitPython with ``mipidsi`` (ESP32-P4) and the community ``gt911``
library (``circup install gt911``).
"""

import time

import board
import busio
import digitalio
import displayio
import framebufferio
import gt911
import mipidsi

from displaysys.fbdisplay import FBDisplay
import eventsys

# This first part is particular to CircuitPython framebuffer-based displays

# Waveshare BSP: SCL=GPIO8, SDA=GPIO7, LCD_RST=GPIO27, BL=GPIO26, TOUCH_RST=GPIO23
I2C_SCL = board.IO8
I2C_SDA = board.IO7
LCD_RESET = board.IO27
LCD_BACKLIGHT = board.IO26
TOUCH_RESET = board.IO23

# ST7703 vendor init (waveshare/esp_lcd_st7703, 720x720 panel)
ST7703_INIT_SEQUENCE = (
    b"\xb9\x03\xf1\x12\x83"
    b"\xb1\x05\x00\x00\x00\xda\x80"
    b"\xb2\x03<\x120"
    b"\xb3\n\x10\x10((\x03\xff\x00\x00\x00\x00"
    b"\xb4\x01\x80"
    b"\xb5\x02\n\n"
    b"\xb6\x02\x97\x97"
    b'\xb8\x04&"\xf0\x13'
    b"\xba\x1b1\x81\x0f\xf9\x0e\x06 \x00\x00\x00\x00\x00\x00\x00D%\x00\x90\n\x00\x00\x01O\x01\x00\x007"
    b"\xbc\x01G"
    b"\xbf\x03\x02\x11\x00"
    b"\xc0\tssPP\x00\x00\x12p\x00"
    b"\xc1\x0c%\x0022w\xe4\xff\xff\xcc\xccww"
    b"\xc6\x06\x82\x00\xbf\xff\x00\xff"
    b"\xc7\x06\xb8\x00\n\x10\x01\t"
    b"\xc8\x04\x10@\x1e\x02"
    b"\xcc\x01\x0b"
    b'\xe0"\x00\x0b\x10,=?B:\x07\r\x0f\x13\x15\x13\x14\x0f\x16\x00\x0b\x10,=?B:\x07\r\x0f\x13\x15\x13\x14\x0f\x16'
    b"\xe3\x0e\x07\x07\x0b\x0b\x0b\x0b\x00\x00\x00\x00\xff\x00\xc0\x10"
    b"\xe9?\xc8\x10\n\x00\x00\x80\x81\x121#O\x86\xa0\x00G\x08\x00\x00\x0c\x00\x00\x00\x00\x00\x0c\x00\x00\x00\x98\x02\x8b\xafF\x02\x88\x88\x88\x88\x88\x98\x13\x8b\xafW\x13\x88\x88\x88\x88\x88\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\xea=\x97\x0c\t\t\tx\x00\x00\x00\x00\x00\x00\x9f1\x8b\xa81u\x88\x88\x88\x88\x88\x9f \x8b\xa8 d\x88\x88\x88\x88\x88#\x00\x00\x02q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x80\x81\x00\x00\x00\x00"
    b"\xef\x03\xff\xff\x01"
    b"\x11\x81\x00\xfa"
    b")\x81\x002"
)

displayio.release_displays()

bus = mipidsi.Bus(frequency=1_000_000_000, num_lanes=2)

reset_pin = digitalio.DigitalInOut(LCD_RESET)
reset_pin.direction = digitalio.Direction.OUTPUT
reset_pin.value = False
time.sleep(0.1)
reset_pin.value = True
time.sleep(0.2)

fb = mipidsi.Display(
    bus,
    init_sequence=ST7703_INIT_SEQUENCE,
    width=720,
    height=720,
    color_depth=16,
    pixel_clock_frequency=38_000_000,
    hsync_pulse_width=20,
    hsync_front_porch=50,
    hsync_back_porch=50,
    vsync_pulse_width=4,
    vsync_front_porch=20,
    vsync_back_porch=20,
    backlight_pin=LCD_BACKLIGHT,
    backlight_on_high=False,
)

display = framebufferio.FramebufferDisplay(fb, auto_refresh=True)
display.root_group = None

i2c = busio.I2C(I2C_SCL, I2C_SDA)
touch_rst = digitalio.DigitalInOut(TOUCH_RESET)
touch_rst.direction = digitalio.Direction.OUTPUT
touch_drv = gt911.GT911(i2c, i2c_address=0x5D, rst_pin=touch_rst)


# Typical board_config.py setup from here on out

display_drv = FBDisplay(fb)


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
