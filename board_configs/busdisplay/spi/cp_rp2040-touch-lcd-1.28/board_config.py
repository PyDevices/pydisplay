"""Waveshare RP2040-Touch-LCD-1.28 GC9A01 240x240 — CircuitPython"""

import board
import busio
from cst816 import CST816
import digitalio
from displayio import release_displays
from fourwire import FourWire
from gc9a01 import GC9A01

import eventsys

release_displays()

# Sticky GPIO backlight (PWM backlight dies on soft-reset / looks blank).
_bl = digitalio.DigitalInOut(board.LCD_BL)
_bl.switch_to_output(value=True)

# Official CP board build exposes LCD_* / IMU_* aliases; no board.SPI()/I2C().
spi = busio.SPI(clock=board.LCD_CLK, MOSI=board.LCD_DIN)
display_bus = FourWire(
    spi,
    command=board.LCD_DC,
    chip_select=board.LCD_CS,
    reset=board.LCD_RST,
    # 60 MHz was flaky on cold boot; Waveshare demos use a lower rate.
    baudrate=10_000_000,
)

display_drv = GC9A01(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=True,
)

# Waveshare GC9A01A: MADCTL 0x98, COLMOD 0x05 (driver init + reinforce).
try:
    display_drv.send(0x36, bytes([0x98]))
    display_drv.send(0x3A, bytes([0x05]))
except Exception:
    try:
        display_bus.send(0x3A, bytes([0x05]))
    except Exception:
        pass

touch_drv = None
touch_read_func = None
touch_rotation_table = (0, 5, 6, 3)

try:
    i2c = busio.I2C(board.IMU_SCL, board.IMU_SDA, frequency=100_000)
    # Touch RST=GP22, IRQ=GP21 (polled; IRQ unused here).
    touch_drv = CST816(i2c, rst_pin=board.GP22)
    touch_read_func = touch_drv.get_point
except Exception:
    touch_drv = None
    touch_read_func = None

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
