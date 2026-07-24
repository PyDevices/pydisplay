"""Waveshare ESP32-S3-Touch-LCD-4.3 — 800x480 RGB565 (ST7262) + GT911

Pin map / timings from ESP32_Display_Panel
``BOARD_WAVESHARE_ESP32_S3_TOUCH_LCD_4_3`` (RGB, no 3-wire SPI control panel).
Backlight + LCD/touch reset via CH422G on I2C (SDA=8, SCL=9).
"""

import time

from ch422g import CH422G
from gt911 import GT911
from machine import I2C, Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    import displayif
except ImportError as exc:
    raise NotImplementedError(
        "Parallel RGB scanout requires displayif.DotClockFramebuffer (esp32 port)"
    ) from exc

# CH422G EXIO map (ESP32_Display_Panel board header)
_TP_RST = 1
_LCD_BL = 2
_LCD_RST = 3
_TP_INT = 4

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400_000)

iox = CH422G(i2c)
iox.enable_all_io_output()
iox.digital_write(_LCD_BL, 1)
# LCD reset (ESP_PANEL_BOARD_LCD_PRE_BEGIN_FUNCTION)
iox.digital_write(_LCD_RST, 0)
time.sleep_ms(10)
iox.digital_write(_LCD_RST, 1)
time.sleep_ms(100)

tft_pins = {
    "de": 5,
    "vsync": 3,
    "hsync": 46,
    "dclk": 7,
    # RGB565 D0..D15 (B0..B4, G0..G5, R0..R4)
    "data": (14, 38, 18, 17, 10, 39, 0, 45, 48, 47, 21, 1, 2, 42, 41, 40),
}

tft_timings = {
    "frequency": 16_000_000,
    "width": 800,
    "height": 480,
    "hsync_pulse_width": 4,
    "hsync_front_porch": 8,
    "hsync_back_porch": 8,
    "vsync_pulse_width": 4,
    "vsync_front_porch": 8,
    "vsync_back_porch": 8,
    "hsync_idle_low": False,
    "vsync_idle_low": False,
    "de_idle_high": False,
    "pclk_active_high": False,  # ESP_PANEL_BOARD_LCD_RGB_PCLK_ACTIVE_NEG = 1
    "pclk_idle_high": False,
}

fb = displayif.DotClockFramebuffer(**tft_pins, **tft_timings)
display_drv = FBDisplay(fb)

# GT911: RST on CH422G EXIO1, INT=GPIO4 (address-select during reset → 0x5D)
touch_drv = GT911(
    i2c,
    reset_pin=iox.Pin(_TP_RST, Pin.OUT, value=1),
    irq_pin=_TP_INT,
    address=0x5D,
    width=800,
    height=480,
    touch_points=5,
    reverse_axis=False,
)


_W = tft_timings["width"]
_H = tft_timings["height"]


def touch_read_func():
    """GT911 reports landscape values with axes reflected over the diagonal.

    Corner calibration (eventsys_touch_coords): TL/BR/center OK; TR↔BL.
    Plain eventsys SWAP_XY is not enough on a non-square panel — rescale
    after the swap so coords stay in 0..width / 0..height.
    """
    n, points = touch_drv.read_points()
    if not n:
        return None
    x, y = points[0][0], points[0][1]
    return y * _W // _H, x * _H // _W


touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
