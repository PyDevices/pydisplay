"""480x480 ST7701 parallel RGB - MicroPython (ESP32-S3)

ST7701 register init uses bit-banged 3-wire SPI via the XL9535 expander.
Pixel scanout uses ``rgbframebuffer.RGBFrameBuffer`` (displayif cmod) and
``displaysys.fbdisplay.FBDisplay``.
"""

from machine import I2C, Pin
from st7701 import LCDPins, run_init
from xl9535 import XL9535

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from rgbframebuffer import RGBFrameBuffer
except ImportError as exc:
    raise NotImplementedError(
        "Parallel RGB scanout requires displayif rgbframebuffer cmod (esp32 port)"
    ) from exc

_PWR_EN = 2
_LCD_CS = 3
_LCD_SDA = 4
_LCD_CLK = 5
_LCD_RST = 6

# 16-pin RGB565 parallel data bus (verify against hardware schematic)
_DATA_PINS = (7, 6, 5, 3, 2, 14, 13, 12, 11, 10, 9, 21, 18, 17, 16, 15)
_HSYNC = 47
_VSYNC = 41
_DE = 45
_PCLK = 42
_BACKLIGHT = 46

tft_pins = {
    "de": _DE,
    "vsync": _VSYNC,
    "hsync": _HSYNC,
    "dclk": _PCLK,
    "data": _DATA_PINS,
}

# Panel timings - tune on hardware when rgbframebuffer driver is available
tft_timings = {
    "frequency": 12_000_000,
    "width": 480,
    "height": 480,
    "hsync_pulse_width": 2,
    "hsync_front_porch": 20,
    "hsync_back_porch": 0,
    "vsync_pulse_width": 8,
    "vsync_front_porch": 30,
    "vsync_back_porch": 1,
    "hsync_idle_low": False,
    "vsync_idle_low": False,
    "de_idle_high": False,
    "pclk_active_high": True,
    "pclk_idle_high": False,
}

i2c = I2C(0, scl=Pin(48), sda=Pin(8))
xl = XL9535(i2c)
_pin_mask = (1 << _PWR_EN) | (1 << _LCD_CS) | (1 << _LCD_SDA) | (1 << _LCD_CLK) | (1 << _LCD_RST)
xl.pinMode8(0, _pin_mask, xl.OUT)
xl.digitalWrite(_PWR_EN, 1)

lcd_pins = LCDPins(
    pwr_en=xl.Pin(_PWR_EN, xl.OUT, value=1),
    cs=xl.Pin(_LCD_CS, xl.OUT, value=1),
    sda=xl.Pin(_LCD_SDA, xl.OUT, value=1),
    clk=xl.Pin(_LCD_CLK, xl.OUT, value=1),
    rst=xl.Pin(_LCD_RST, xl.OUT, value=1),
)
run_init(lcd_pins)

backlight = Pin(_BACKLIGHT, Pin.OUT, value=1)

fb = RGBFrameBuffer(**tft_pins, **tft_timings)
display_drv = FBDisplay(fb)

runtime = None
