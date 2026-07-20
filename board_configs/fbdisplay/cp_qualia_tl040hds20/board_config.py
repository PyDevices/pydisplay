"""Qualia S3 RGB-666 with TL040HDS20 4.0" 720x720 Square Display

Paint path matches Adafruit CircuitPython Qualia RGB666 examples:

* ``DotClockFramebuffer`` — panel framebuffer in **PSRAM** (SPIRAM)
* ``displayio.Bitmap`` — software surface also in PSRAM
* ``bitmaptools`` — C blit/fill into the Bitmap
* ``FramebufferDisplay.refresh`` — C composite into the DotClock buffer

Touch on the TL040HDS20 is at I2C address ``0x48`` (not the default 0x38).
"""

from adafruit_focaltouch import Adafruit_FocalTouch
import board
import busio
import displayio
import dotclockframebuffer
import framebufferio

from displaysys.fbdisplay import FBDisplay
import eventsys

tft_pins = dict(board.TFT_PINS)

tft_timings = {
    "frequency": 16_000_000,
    "width": 720,
    "height": 720,
    "hsync_pulse_width": 2,
    "hsync_front_porch": 46,
    "hsync_back_porch": 44,
    "vsync_pulse_width": 2,
    "vsync_front_porch": 16,
    "vsync_back_porch": 18,
    "hsync_idle_low": False,
    "vsync_idle_low": False,
    "de_idle_high": False,
    "pclk_active_high": False,
    "pclk_idle_high": False,
}

init_sequence_tl040hds20 = bytes()

displayio.release_displays()

board.I2C().deinit()
i2c = busio.I2C(board.SCL, board.SDA, frequency=100_000)
tft_io_expander = dict(board.TFT_IO_EXPANDER)
# tft_io_expander["i2c_address"] = 0x38  # uncomment for Qualia rev B
dotclockframebuffer.ioexpander_send_init_sequence(i2c, init_sequence_tl040hds20, **tft_io_expander)

fb = dotclockframebuffer.DotClockFramebuffer(**tft_pins, **tft_timings)

# Adafruit Qualia path: displayio auto-refreshes at the panel rate. Manual
# refresh() from LVGL every ~30ms tears against the free-running DPI scanout.
display = framebufferio.FramebufferDisplay(fb, auto_refresh=True)

# PSRAM Bitmap — CircuitPython allocates large bitmaps from SPIRAM when present.
_bitmap = displayio.Bitmap(tft_timings["width"], tft_timings["height"], 65535)
_tile = displayio.TileGrid(
    _bitmap,
    pixel_shader=displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565),
)
_group = displayio.Group()
_group.append(_tile)
display.root_group = _group

display_drv = FBDisplay(fb, bitmap=_bitmap, display=display)

touch_drv = Adafruit_FocalTouch(i2c, address=0x48)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
    # Sync + multimer polling Timer: CircuitPython has no machine.Timer and
    # (on this build) no frozen asyncio — timer_async would use _mpasyncio and
    # leave LVGL unarmed / blank after ``import lv_test_timer``.
    timer_async=False,
)
