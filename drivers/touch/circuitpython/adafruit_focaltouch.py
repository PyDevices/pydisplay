# SPDX-FileCopyrightText: 2017 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_focaltouch`
====================================================

CircuitPython driver for common low-cost FocalTech capacitive touch chips.
Currently supports FT6206, FT6236 & FT6336.

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* Adafruit `2.8" TFT LCD with Cap Touch Breakout Board w/MicroSD Socket
  <http://www.adafruit.com/product/2090>`_ (Product ID: 2090)

* Adafruit `2.8" TFT Touch Shield for Arduino w/Capacitive Touch
  <http://www.adafruit.com/product/1947>`_ (Product ID: 1947)

* M5Stack Core2 and CoreS3

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library (when using I2C/SPI):
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# imports

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FocalTouch.git"

import contextlib
import struct

from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const

with contextlib.suppress(ImportError):
    from typing import List


_FT_DEFAULT_I2C_ADDR = 0x38

_FT_REG_DATA = const(0x00)
_FT_REG_NUMTOUCHES = const(0x02)
_FT_REG_THRESHHOLD = const(0x80)
_FT_REG_POINTRATE = const(0x88)
_FT_REG_LIBH = const(0xA1)
_FT_REG_LIBL = const(0xA2)
_FT_REG_CHIPID = const(0xA3)
_FT_REG_FIRMVERS = const(0xA6)
_FT_REG_VENDID = const(0xA8)
_FT_REG_RELEASE = const(0xAF)

_FT6XXX_TOUCH_BUFFER_SIZE = 32
_FT6XXX_SCALE_FACTOR = (1.0, 1.0)

_FT5X06_TOUCH_BUFFER_SIZE = 63
_FT5X06_SCALE_FACTOR = (2.24, 2.14)  # (x,y) scaling factors


class Adafruit_FocalTouch:
    """
    A driver for the FocalTech capacitive touch sensor.
    """

    def __init__(self, i2c, address=_FT_DEFAULT_I2C_ADDR, debug=False, irq_pin=None):
        self._i2c = I2CDevice(i2c, address)
        self._debug = debug
        self._irq_pin = irq_pin

        chip_data = self._read(_FT_REG_LIBH, 8)  # don't wait for IRQ
        # print("chip_data: {%x}".format(chip_data))
        lib_ver, chip_id, _, _, firm_id, _, vend_id = struct.unpack(">HBBBBBB", chip_data)
        if debug:
            print(
                "lib_ver: {:02X}, chip_id: {:02X}, firm_id: {:02X}, vend_id: {:02X}".format(
                    lib_ver, chip_id, firm_id, vend_id
                )
            )

        if vend_id not in (0x11, 0x42, 0x01):
            raise RuntimeError("Did not find FT chip")

        if chip_id == 0x06:
            self.chip = "FT6206"
            self._touch_buffer_size = _FT6XXX_TOUCH_BUFFER_SIZE
            self._scale_factor = _FT6XXX_SCALE_FACTOR
        elif chip_id in (0x64, 0x36):
            self.chip = "FT6236"
            self._touch_buffer_size = _FT6XXX_TOUCH_BUFFER_SIZE
            self._scale_factor = _FT6XXX_SCALE_FACTOR
        elif chip_id == 0x55:
            self.chip = "FT5x06"
            self._touch_buffer_size = _FT5X06_TOUCH_BUFFER_SIZE
            self._scale_factor = _FT5X06_SCALE_FACTOR

        if debug:
            print("Library vers %04X" % lib_ver)
            print("Firmware ID %02X" % firm_id)
            print("Point rate %d Hz" % self._read(_FT_REG_POINTRATE, 1)[0])
            print("Thresh %d" % self._read(_FT_REG_THRESHHOLD, 1)[0])

    @property
    def touched(self) -> int:
        """Returns the number of touches currently detected"""
        return self._read(_FT_REG_NUMTOUCHES, 1, irq_pin=self._irq_pin)[0]

    # pylint: disable=unused-variable
    @property
    def touches(self) -> List[dict]:
        """
        Returns a list of touchpoint dicts, with 'x' and 'y' containing the
        touch coordinates, and 'id' as the touch # for multitouch tracking
        """
        touchpoints = []
        data = self._read(_FT_REG_DATA, self._touch_buffer_size, irq_pin=self._irq_pin)

        touchcount = data[_FT_REG_NUMTOUCHES - _FT_REG_DATA]
        if self._debug:
            print("touchcount: {}".format(touchcount))

        for i in range(touchcount):
            point_data = data[i * 6 + 3 : i * 6 + 9]
            if all(i == 255 for i in point_data):
                continue
            # print([hex(i) for i in point_data])
            x, y, _weight, _misc = struct.unpack(">HHBB", point_data)
            # print(x, y, weight, misc)
            touch_id = y >> 12
            x = round((x & 0xFFF) / self._scale_factor[0])
            y = round((y & 0xFFF) / self._scale_factor[1])
            point = {"x": x, "y": y, "id": touch_id}
            if self._debug:
                print("id: {}, x: {}, y: {}".format(touch_id, x, y))
            touchpoints.append(point)
        return touchpoints

    def _read(self, register, length, irq_pin=None) -> bytearray:
        """Returns an array of 'length' bytes from the 'register'"""
        with self._i2c as i2c:
            if irq_pin is not None:
                while irq_pin.value:
                    pass

            i2c.write(bytes([register & 0xFF]))
            result = bytearray(length)

            i2c.readinto(result)
            if self._debug:
                print("\t$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write(self, register, values) -> None:
        """Writes an array of 'length' bytes to the 'register'"""
        with self._i2c as i2c:
            values = [(v & 0xFF) for v in [register] + values]  # noqa: RUF005
            if self._debug:
                print("register: %02X, value: %02X" % (values[0], values[1]))
            i2c.write(bytes(values))

            if self._debug:
                print("\t$%02X <= %s" % (values[0], [hex(i) for i in values[1:]]))
