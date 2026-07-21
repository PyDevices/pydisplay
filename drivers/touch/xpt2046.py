"""XPT2046 resistive touch controller (MicroPython).

Read sequence matches LilyGO arduino_xpt2046 (``SPI.transfer16`` frames,
IRQ active-low with pull-up). Press = IRQ low or |z| above threshold.
"""

from time import sleep

from machine import Pin
from micropython import const


def _besttwoavg(x, y, z):
    da = x - y if x > y else y - x
    db = x - z if x > z else z - x
    dc = z - y if z > y else y - z
    if da <= db and da <= dc:
        return (x + y) >> 1
    if db <= da and db <= dc:
        return (x + z) >> 1
    return (y + z) >> 1


# Module-level (not class ``const``): MicroPython may optimize underscore
# ``const`` class attrs away; bare names are safer for runtime thresholds.
_Z_THRESHOLD = 25


class Touch(object):
    """Serial interface for XPT2046 Touch Screen Controller."""

    CMD_X = const(0x90)
    CMD_Y = const(0xD0)
    CMD_Z1 = const(0xB0)
    CMD_Z2 = const(0xC0)

    def __init__(self, spi, cs, int_pin=None, int_handler=None):
        self.spi = spi
        self.cs = cs
        self.cs.init(self.cs.OUT, value=1)
        self.cal = False
        self.tx16 = bytearray(2)
        self.rx16 = bytearray(2)
        self.int_pin = None
        if int_pin is not None:
            self.int_pin = int_pin
            self.int_pin.init(Pin.IN, Pin.PULL_UP)
        if int_handler is not None:
            self.int_handler = int_handler
            self.int_locked = False
            int_pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.int_press)

    def set_orientation(self, orientation):
        self.orientation = orientation

    def int_press(self, pin):
        if not pin.value() and not self.int_locked:
            self.int_locked = True
            x, y = self.get_touch()
            self.int_handler(x, y)
            sleep(0.1)
        elif pin.value() and self.int_locked:
            sleep(0.1)
            self.int_locked = False

    def calibrate(self, xmin, xmax, ymin, ymax, width, height, orientation):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.orientation = orientation
        if self.orientation % 2 == 0:
            self.width = height
            self.height = width
        else:
            self.width = width
            self.height = height
        self.cal = True

    def _transfer16(self, value):
        self.tx16[0] = (value >> 8) & 0xFF
        self.tx16[1] = value & 0xFF
        self.spi.write_readinto(self.tx16, self.rx16)
        return (self.rx16[0] << 8) | self.rx16[1]

    def _sample(self):
        """CS-held conversion → z, xraw, yraw (LilyGO ``pressed`` sequence)."""
        self.cs(0)
        z1 = self._transfer16(self.CMD_Z1) >> 4
        z2 = self._transfer16(self.CMD_Z2) >> 4
        z = abs(z1) - abs(z2)
        x0 = self._transfer16(self.CMD_X) >> 4
        y0 = self._transfer16(self.CMD_Y) >> 4
        x1 = self._transfer16(self.CMD_X) >> 4
        y1 = self._transfer16(self.CMD_Y) >> 4
        x2 = self._transfer16(self.CMD_X) >> 4
        y2 = self._transfer16(self.CMD_Y) >> 4
        self._transfer16(0)
        self.cs(1)
        return z, _besttwoavg(x0, x1, x2), _besttwoavg(y0, y1, y2)

    def raw_touch(self):
        _z, x, y = self._sample()
        return x, y

    def map_value(self, v, vmin, vmax, maxv):
        if vmax == vmin:
            return 0
        return int((v - vmin) / (vmax - vmin) * maxv)

    def _map_raw(self, xraw, yraw, clip=False):
        x = self.map_value(xraw, self.xmin, self.xmax, self.width)
        y = self.map_value(yraw, self.ymin, self.ymax, self.height)
        if clip:
            x = max(0, min(x, self.width - 1))
            y = max(0, min(y, self.height - 1))
        if self.orientation % 2 == 1:
            return y, self.width - x
        return x, y

    def get_touch(self, clip=False):
        if not self.cal:
            print("Touch is not calibrated: use raw_touch or calibrate")
            return 0, 0
        return self._map_raw(*self.raw_touch(), clip=clip)

    def is_touched(self):
        if self.int_pin is not None and self.int_pin.value() == 0:
            return True
        z, _x, _y = self._sample()
        return abs(z) >= _Z_THRESHOLD

    def read_point(self, clip=True):
        """One sample: ``None`` if up, else ``(x, y)``."""
        irq = self.int_pin is not None and self.int_pin.value() == 0
        z, xraw, yraw = self._sample()
        if not irq and abs(z) < _Z_THRESHOLD:
            return None
        if not self.cal:
            return 0, 0
        return self._map_raw(xraw, yraw, clip=clip)
