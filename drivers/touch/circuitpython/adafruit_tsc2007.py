# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_tsc2007`
================================================================================

Python library for TSC2007 resistive touch screen driver


* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* Works with the Adafruit TSC2007 resistive touch driver.
  `Purchase one from the Adafruit shop <http://www.adafruit.com/products/5423>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

import digitalio
from adafruit_bus_device import i2c_device

try:
    # Used only for typing
    from typing import Union

    import busio
except ImportError:
    pass




TSC2007_MEASURE_TEMP0 = 0
TSC2007_MEASURE_AUX = 2
TSC2007_MEASURE_TEMP1 = 4
TSC2007_ACTIVATE_X = 8
TSC2007_ACTIVATE_Y = 9
TSC2007_ACTIVATE_YPLUS_X = 10
TSC2007_SETUP_COMMAND = 11
TSC2007_MEASURE_X = 12
TSC2007_MEASURE_Y = 13
TSC2007_MEASURE_Z1 = 14
TSC2007_MEASURE_Z2 = 15

TSC2007_POWERDOWN_IRQON = 0
TSC2007_ADON_IRQOFF = 1
TSC2007_ADOFF_IRQON = 2

TSC2007_ADC_12BIT = 0
TSC2007_ADC_8BIT = 1


class TSC2007:
    """
    A driver for the TSC2007 resistive touch sensor.
    """

    def __init__(
        self,
        i2c: busio.I2C,
        address: int = 0x48,
        irq: Union[int | None] = None,
        invert_x: bool = False,
        invert_y: bool = False,
        swap_xy: bool = False,
    ):
        self._i2c = i2c_device.I2CDevice(i2c, address)
        self._irq = irq
        if self._irq:
            self._irq.switch_to_input(pull=digitalio.Pull.UP)
        self._buf = bytearray(2)
        self._cmd = bytearray(1)

        # Settable Properties
        self._invert_x = invert_x
        self._invert_y = invert_y
        self._swap_xy = swap_xy

        self.touch

    def command(self, function: int, power: int, resolution: int) -> int:
        """
        Write a command byte to the TSC2007 and read the 2-byte response
        """
        if not 0 <= function <= 15:
            raise RuntimeError("Function setting must be between 0 and 15")
        if not 0 <= power <= 3:
            raise RuntimeError("Power setting must be between 0 and 3")
        if not 0 <= resolution <= 1:
            raise RuntimeError("Power setting must be ADC_8BIT or ADC_12BIT")

        self._cmd[0] = (function & 0x0F) << 4
        self._cmd[0] |= (power & 0x03) << 2
        self._cmd[0] |= (resolution & 0x01) << 1

        with self._i2c as i2c:
            i2c.write_then_readinto(self._cmd, self._buf)
        return (self._buf[0] << 4) | (self._buf[1] >> 4)  # 12 bits of data!

    @property
    def touched(self) -> bool:
        """Returns whether the panel is touched. If irq pin is set, uses
        the pin value. If not, the TSC2007 is polled and pressure is checked"""
        if self._irq:
            return not self._irq.value
        point = self.touch
        return point["pressure"] > 100

    @property
    def touch(self) -> dict:
        """Returns the current touch point"""
        x = self.command(TSC2007_MEASURE_X, TSC2007_ADON_IRQOFF, TSC2007_ADC_12BIT)
        y = self.command(TSC2007_MEASURE_Y, TSC2007_ADON_IRQOFF, TSC2007_ADC_12BIT)
        z = self.command(TSC2007_MEASURE_Z1, TSC2007_ADON_IRQOFF, TSC2007_ADC_12BIT)
        self.command(TSC2007_MEASURE_TEMP0, TSC2007_POWERDOWN_IRQON, TSC2007_ADC_12BIT)

        if self._invert_x:
            x = 4095 - x

        if self._invert_y:
            y = 4095 - y

        if self._swap_xy:
            x, y = y, x

        point = {"x": x, "y": y, "pressure": z}
        return point

    @property
    def invert_x(self) -> bool:
        """Whether the X axis is inverted"""
        return self._invert_x

    @invert_x.setter
    def invert_x(self, value: bool):
        self._invert_x = value

    @property
    def invert_y(self) -> bool:
        """Whether the Y axis is inverted"""
        return self._invert_y

    @invert_y.setter
    def invert_y(self, value: bool):
        self._invert_y = value

    @property
    def swap_xy(self) -> bool:
        """Whether the X and Y axes are swapped"""
        return self._swap_xy

    @swap_xy.setter
    def swap_xy(self, value: bool):
        self._swap_xy = value
