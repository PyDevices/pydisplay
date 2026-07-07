"""NXP MIMXRT1060-EVK + RK043FN66HS-CTG 4.3\" parallel RGB — MicroPython

Hardware (plug-in, no breadboard wiring):
- MIMXRT1060-EVK / EVKB: https://circuitpython.org/board/imxrt1060_evk/
- RK043FN66HS-CTG shield on J49 (40-pin parallel FPC + 6-pin touch I2C)

Targets displayif ``rgbframebuffer`` (NXP eLCDIF) on mimxrt.  Pin names match
CircuitPython ``board.LCD_*`` on imxrt1060_evk; MicroPython uses ``GPIO_B*`` cpu
pin names from the NXP EVK LCDIF mux (MCUXpresso BOARD_InitLCDPins).

CircuitPython sibling: ``cp_mimxrt1060_evk_rk043_rgb``.
"""

from machine import Pin
import time

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from rgbframebuffer import RGBFrameBuffer
except ImportError as exc:
    raise NotImplementedError(
        "Parallel RGB scanout requires displayif rgbframebuffer cmod (mimxrt eLCDIF)"
    ) from exc

# RK043 panel control (EVK routes through shield / EVK GPIO)
LCD_BACKLIGHT = Pin("GPIO_B1_15", Pin.OUT, value=1)
LCD_RESET = Pin("GPIO_AD_B0_02", Pin.OUT, value=1)

LCD_RESET.value(0)
time.sleep_ms(10)
LCD_RESET.value(1)
time.sleep_ms(120)

# 16-bit RGB565 on LCD_D0..LCD_D15 (NXP SDK default for this shield)
tft_pins = {
    "de": Pin("GPIO_B0_01"),
    "vsync": Pin("GPIO_B0_03"),
    "hsync": Pin("GPIO_B0_02"),
    "dclk": Pin("GPIO_B0_00"),
    "data": (
        Pin("GPIO_B0_04"),
        Pin("GPIO_B0_05"),
        Pin("GPIO_B0_06"),
        Pin("GPIO_B0_07"),
        Pin("GPIO_B0_08"),
        Pin("GPIO_B0_09"),
        Pin("GPIO_B0_10"),
        Pin("GPIO_B0_11"),
        Pin("GPIO_B0_12"),
        Pin("GPIO_B0_13"),
        Pin("GPIO_B0_14"),
        Pin("GPIO_B0_15"),
        Pin("GPIO_B1_00"),
        Pin("GPIO_B1_01"),
        Pin("GPIO_B1_02"),
        Pin("GPIO_B1_03"),
    ),
}

# Timings from NXP ELCDIF_RgbModeGetDefaultConfig (480×272 RK043)
tft_timings = {
    "frequency": 9_000_000,
    "width": 480,
    "height": 272,
    "hsync_pulse_width": 41,
    "hsync_front_porch": 4,
    "hsync_back_porch": 8,
    "vsync_pulse_width": 10,
    "vsync_front_porch": 4,
    "vsync_back_porch": 2,
    "hsync_idle_low": True,
    "vsync_idle_low": True,
    "de_idle_high": False,
    "pclk_active_high": False,
    "pclk_idle_high": False,
}

fb = RGBFrameBuffer(**tft_pins, **tft_timings)

display_drv = FBDisplay(fb)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
