"""Waveshare ESP32-P4-WIFI6-Touch-LCD-4B - MicroPython

720x720 ST7703 on MIPI DSI + GT911 touch.  Targets the displayif ``mipidsi``
cmod on ESP32-P4.  The ``Bus`` / ``Display`` call surface mirrors CircuitPython
``mipidsi``; ``Display`` must satisfy the ``FBDisplay`` buffer contract
(``.width``, ``.height``, ``memoryview()``, ``.refresh()``).

displayif implementation notes (Waveshare BSP):
- Enable DSI PHY LDO channel 3 at 2500 mV before ``esp_lcd_new_dsi_bus``
- Lane bit rate 1000 Mbps/lane, 2 lanes
- ``refresh()`` should flush CPU cache then ``esp_lcd_panel_draw_bitmap`` (CP mipidsi)

CircuitPython sibling: ``cp_esp32-p4-wifi6-touch-lcd-4b``.

BSP reference: waveshareteam/Waveshare-ESP32-components ``esp32_p4_wifi6_touch_lcd_4b``
"""

import time

from gt911 import GT911
from machine import I2C, Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError("MIPI DSI requires displayif mipidsi cmod (esp32p4 port)") from exc

# Waveshare BSP pinout
LCD_RESET = 27
LCD_BACKLIGHT = 26
I2C_SCL = 8
I2C_SDA = 7
TOUCH_RESET = 23
# GT911 INT is not routed to the MCU (BSP: GPIO_NC); GPIO22 is unused dummy for reset.
TOUCH_IRQ_DUMMY = 22

# ST7703 vendor init (waveshare/esp_lcd_st7703, 720x720 panel).
# Init record format matches CircuitPython busdisplay / mipidsi:
#   bytes([cmd, param_count | 0x80, ...params..., delay_ms])
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

# MIPI DSI bus (BSP_LCD_MIPI_DSI_LANE_BITRATE_MBPS = 1000)
bus = Bus(frequency=1_000_000_000, num_lanes=2)

lcd_reset = Pin(LCD_RESET, Pin.OUT, value=1)
lcd_reset.value(0)
time.sleep_ms(100)
lcd_reset.value(1)
time.sleep_ms(200)

# DPI timings from ST7703_720_720_PANEL_60HZ_DPI_CONFIG
fb = Display(
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
    reset_pin=LCD_RESET,
    backlight_pin=LCD_BACKLIGHT,
    backlight_on_high=False,
)

i2c = I2C(1, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400_000)
touch_drv = GT911(
    i2c,
    reset_pin=TOUCH_RESET,
    irq_pin=TOUCH_IRQ_DUMMY,
    address=0x5D,
    width=720,
    height=720,
    touch_points=5,
)


def touch_read_func():
    n, points = touch_drv.read_points()
    if n:
        return points[0][0], points[0][1]
    return None


display_drv = FBDisplay(fb)

touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
