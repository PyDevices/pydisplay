# SPDX-FileCopyrightText: 2017, 2022 Jerry Needell for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_stmpe610`
====================================================
This is a CircuitPython Driver for the STMPE610 Resistive Touch sensor

* Author(s): Jerry Needell, CedarGroveMakerStudios

Implementation Notes
--------------------
**Hardware:**

* 2.4" 320x240 TFT FeatherWing display: https://www.adafruit.com/product/3315
* 3.5" 480x320 TFT FeatherWing display: https://www.adafruit.com/product/3651
* Resistive Touch Screen Controller - STMPE610 breakout board:
  https://www.adafruit.com/product/1571  (discontinued)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

import time

from micropython import const

try:
    from typing import Dict, List, Optional, Tuple

    from busio import I2C, SPI
    from microcontroller import Pin
    from typing_extensions import Literal
except ImportError:
    pass





def map_range(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """
    Maps a value from one range to another. Values beyond the input minimum or
    maximum will be limited to the minimum or maximum of the output range.

    :return: Returns value mapped to new range
    :rtype: float
    """
    in_range = in_max - in_min
    in_delta = x - in_min
    if in_range != 0:
        mapped = in_delta / in_range
    elif in_delta != 0:
        mapped = in_delta
    else:
        mapped = 0.5
    mapped *= out_max - out_min
    mapped += out_min
    if out_min <= out_max:
        return max(min(mapped, out_max), out_min)
    return min(max(mapped, out_max), out_min)


_STMPE_ADDR = const(0x41)
_STMPE_VERSION = const(0x0811)

_STMPE_SYS_CTRL1 = const(0x03)
_STMPE_SYS_CTRL1_RESET = const(0x02)
_STMPE_SYS_CTRL2 = const(0x04)

_STMPE_TSC_CTRL = const(0x40)
_STMPE_TSC_CTRL_EN = const(0x01)
_STMPE_TSC_CTRL_XYZ = const(0x00)
_STMPE_TSC_CTRL_XY = const(0x02)

_STMPE_INT_CTRL = const(0x09)
_STMPE_INT_CTRL_POL_HIGH = const(0x04)
_STMPE_INT_CTRL_POL_LOW = const(0x00)
_STMPE_INT_CTRL_EDGE = const(0x02)
_STMPE_INT_CTRL_LEVEL = const(0x00)
_STMPE_INT_CTRL_ENABLE = const(0x01)
_STMPE_INT_CTRL_DISABLE = const(0x00)


_STMPE_INT_EN = const(0x0A)
_STMPE_INT_EN_TOUCHDET = const(0x01)
_STMPE_INT_EN_FIFOTH = const(0x02)
_STMPE_INT_EN_FIFOOF = const(0x04)
_STMPE_INT_EN_FIFOFULL = const(0x08)
_STMPE_INT_EN_FIFOEMPTY = const(0x10)
_STMPE_INT_EN_ADC = const(0x40)
_STMPE_INT_EN_GPIO = const(0x80)

_STMPE_INT_STA = const(0x0B)
_STMPE_INT_STA_TOUCHDET = const(0x01)

_STMPE_ADC_CTRL1 = const(0x20)
_STMPE_ADC_CTRL1_12BIT = const(0x08)
_STMPE_ADC_CTRL1_10BIT = const(0x00)

_STMPE_ADC_CTRL2 = const(0x21)
_STMPE_ADC_CTRL2_1_625MHZ = const(0x00)
_STMPE_ADC_CTRL2_3_25MHZ = const(0x01)
_STMPE_ADC_CTRL2_6_5MHZ = const(0x02)

_STMPE_TSC_CFG = const(0x41)
_STMPE_TSC_CFG_1SAMPLE = const(0x00)
_STMPE_TSC_CFG_2SAMPLE = const(0x40)
_STMPE_TSC_CFG_4SAMPLE = const(0x80)
_STMPE_TSC_CFG_8SAMPLE = const(0xC0)
_STMPE_TSC_CFG_DELAY_10US = const(0x00)
_STMPE_TSC_CFG_DELAY_50US = const(0x08)
_STMPE_TSC_CFG_DELAY_100US = const(0x10)
_STMPE_TSC_CFG_DELAY_500US = const(0x18)
_STMPE_TSC_CFG_DELAY_1MS = const(0x20)
_STMPE_TSC_CFG_DELAY_5MS = const(0x28)
_STMPE_TSC_CFG_DELAY_10MS = const(0x30)
_STMPE_TSC_CFG_DELAY_50MS = const(0x38)
_STMPE_TSC_CFG_SETTLE_10US = const(0x00)
_STMPE_TSC_CFG_SETTLE_100US = const(0x01)
_STMPE_TSC_CFG_SETTLE_500US = const(0x02)
_STMPE_TSC_CFG_SETTLE_1MS = const(0x03)
_STMPE_TSC_CFG_SETTLE_5MS = const(0x04)
_STMPE_TSC_CFG_SETTLE_10MS = const(0x05)
_STMPE_TSC_CFG_SETTLE_50MS = const(0x06)
_STMPE_TSC_CFG_SETTLE_100MS = const(0x07)

_STMPE_FIFO_TH = const(0x4A)

_STMPE_FIFO_SIZE = const(0x4C)

_STMPE_FIFO_STA = const(0x4B)
_STMPE_FIFO_STA_RESET = const(0x01)
_STMPE_FIFO_STA_OFLOW = const(0x80)
_STMPE_FIFO_STA_FULL = const(0x40)
_STMPE_FIFO_STA_EMPTY = const(0x20)
_STMPE_FIFO_STA_THTRIG = const(0x10)

_STMPE_TSC_I_DRIVE = const(0x58)
_STMPE_TSC_I_DRIVE_20MA = const(0x00)
_STMPE_TSC_I_DRIVE_50MA = const(0x01)

_STMPE_TSC_DATA_X = const(0x4D)
_STMPE_TSC_DATA_Y = const(0x4F)
_STMPE_TSC_FRACTION_Z = const(0x56)

_STMPE_GPIO_SET_PIN = const(0x10)
_STMPE_GPIO_CLR_PIN = const(0x11)
_STMPE_GPIO_DIR = const(0x13)
_STMPE_GPIO_ALT_FUNCT = const(0x17)


class Adafruit_STMPE610:
    """A class (driver) for the STMPE610 Resistive Touch controller used by the
    2.4" 320x240 TFT FeatherWing display (#3315), 3.5" 480x320 TFT FeatherWing
    display (#3651), and the Resistive Touch Screen Controller - STMPE610
    breakout board (#1571). This class acts as a super class for the I2C and
    SPI interface classes.

    This class was modified from the original to add the Displayio Button
    compatible touch_point property to the existing functionality.

    See the examples folder for instantiation kwargs and properties."""

    def __init__(self) -> None:
        """Reset the controller."""
        self._write_register_byte(_STMPE_SYS_CTRL1, _STMPE_SYS_CTRL1_RESET)
        time.sleep(0.001)

        self._write_register_byte(_STMPE_SYS_CTRL2, 0x0)  # turn on clocks!
        self._write_register_byte(
            _STMPE_TSC_CTRL, _STMPE_TSC_CTRL_XYZ | _STMPE_TSC_CTRL_EN
        )  # XYZ and enable!
        self._write_register_byte(_STMPE_INT_EN, _STMPE_INT_EN_TOUCHDET)
        self._write_register_byte(
            _STMPE_ADC_CTRL1, _STMPE_ADC_CTRL1_10BIT | (0x6 << 4)
        )  # 96 clocks per conversion
        self._write_register_byte(_STMPE_ADC_CTRL2, _STMPE_ADC_CTRL2_6_5MHZ)
        self._write_register_byte(
            _STMPE_TSC_CFG,
            _STMPE_TSC_CFG_4SAMPLE | _STMPE_TSC_CFG_DELAY_1MS | _STMPE_TSC_CFG_SETTLE_5MS,
        )
        self._write_register_byte(_STMPE_TSC_FRACTION_Z, 0x6)
        self._write_register_byte(_STMPE_FIFO_TH, 1)
        self._write_register_byte(_STMPE_FIFO_STA, _STMPE_FIFO_STA_RESET)
        self._write_register_byte(_STMPE_FIFO_STA, 0)  # Unreset
        self._write_register_byte(_STMPE_TSC_I_DRIVE, _STMPE_TSC_I_DRIVE_50MA)
        self._write_register_byte(_STMPE_INT_STA, 0xFF)  # Reset all ints
        self._write_register_byte(
            _STMPE_INT_CTRL, _STMPE_INT_CTRL_POL_HIGH | _STMPE_INT_CTRL_ENABLE
        )

    def read_data(self) -> Tuple[int, int, int]:
        """Request next stored reading - return tuple containing (x,y,pressure)."""
        d_1 = self._read_byte(0xD7)
        d_2 = self._read_byte(0xD7)
        d_3 = self._read_byte(0xD7)
        d_4 = self._read_byte(0xD7)
        x_loc = d_1 << 4 | d_2 >> 4
        y_loc = (d_2 & 0xF) << 8 | d_3
        pressure = d_4
        # Reset all ints  (not sure what this does)
        if self.buffer_empty:
            self._write_register_byte(_STMPE_INT_STA, 0xFF)
        return (x_loc, y_loc, pressure)

    def _read_byte(self, register: int) -> int:
        """Read a byte register value and return it."""
        return self._read_register(register, 1)[0]

    def _read_register(self, register: int, length: int) -> bytearray:
        """Read an arbitrarily long register (specified by length number of
        bytes) and return a bytearray of the retrieved data.
        Subclasses MUST implement this!"""
        raise NotImplementedError

    def _write_register_byte(self, register: int, value: int) -> None:
        """Write a single byte register at the specified register address.
        Subclasses MUST implement this!"""
        raise NotImplementedError

    @property
    def touches(self) -> List[Dict[str, int]]:
        """Returns a list of touchpoint dicts, with 'x' and 'y' containing the
        touch coordinates, and 'pressure'."""
        touchpoints = []
        while (len(touchpoints) < 4) and not self.buffer_empty:
            (x_loc, y_loc, pressure) = self.read_data()
            point = {"x": x_loc, "y": y_loc, "pressure": pressure}
            touchpoints.append(point)
        return touchpoints

    @property
    def get_version(self) -> int:
        """Read the version number from the sensor."""
        v_1 = self._read_byte(0)
        v_2 = self._read_byte(1)
        version = v_1 << 8 | v_2
        # print("version ",hex(version))
        return version

    @property
    def touched(self) -> bool:
        """Report if any touches were detected."""
        touch = self._read_byte(_STMPE_TSC_CTRL) & 0x80
        return touch == 0x80

    @property
    def buffer_size(self) -> int:
        """The amount of touch data in the buffer."""
        return self._read_byte(_STMPE_FIFO_SIZE)

    @property
    def buffer_empty(self) -> bool:
        """Buffer empty status."""
        empty = self._read_byte(_STMPE_FIFO_STA) & _STMPE_FIFO_STA_EMPTY
        return empty != 0

    @property
    def get_point(self) -> Dict[str, int]:
        """Read one touch from the buffer."""
        (x_loc, y_loc, pressure) = self.read_data()
        point = {"x": x_loc, "y": y_loc, "pressure": pressure}
        return point


class Adafruit_STMPE610_I2C(Adafruit_STMPE610):
    """I2C interface class for the STMPE610 Resistive Touch sensor.

    :param i2c: I2C interface bus
    :param int address: I2C address. Defaults to 0x41
    :param None, (int, int) calibration: touchscreen calibration tuple.
     Defaults to None.
    :param None, (int, int) size: display size tuple (width, height).
     Defaults to None.
    :param int disp_rotation: display rotation in degrees. Values allowed are
     0, 90, 180, and 270. Defaults to 0.
    :param (bool, bool) touch_flip: swap touchscreen axis range minimum and
     maximum values for (x, y) axes as referenced to display 0-degree rotation.
     Defaults to (False, False).

    ** Quickstart: Importing and instantiating Adafruit_STMPE610_I2C**

    Import the Adafruit_STMPE610_I2C class and instantiate for the 2.4" TFT Wing
    after instantiating the display:

    .. code-block:: python

        import adafruit_stmpe610
        ts = adafruit_stmpe610.Adafruit_STMPE610_I2C(board.I2C(), address=0x41,
            calibration=((357, 3812), (390, 3555)),
            size=(display.width, display.height), disp_rotation=display.rotation,
            touch_flip=(False, False))

    """

    def __init__(
        self,
        i2c: I2C,
        address: int = _STMPE_ADDR,
        calibration: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
        size: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
        disp_rotation: Literal[0, 90, 180, 270] = 0,
        touch_flip: Tuple[bool, bool] = (False, False),
    ) -> None:
        self._calib = calibration
        self._disp_size = size
        self._disp_rotation = disp_rotation
        self._touch_flip = touch_flip

        # Check the touchscreen calibration and display size kwargs.
        if not self._calib:
            self._calib = ((0, 4095), (0, 4095))
        if not self._disp_size:
            self._disp_size = (4095, 4095)

        if self._disp_rotation not in {0, 90, 180, 270}:
            raise ValueError("Display rotation value must be 0, 90, 180, or 270")

        # Check that the STMPE610 was found.
        import adafruit_bus_device.i2c_device as i2cdev

        self._i2c = i2cdev.I2CDevice(i2c, address)
        # Check device version.
        version = self.get_version
        if _STMPE_VERSION != version:
            raise RuntimeError(f"Failed to find STMPE610! Chip Version {hex(version).upper()}.")
        super().__init__()

    @property
    def touch_point(
        self,
    ) -> Optional[Tuple[int, int, int]]:
        """Read latest touched point value and convert to calibration-adjusted
        and rotated display coordinates. Commpatible with Displayio Button.
        :return: x, y, pressure
        rtype: int, int, int
        """
        if not self.buffer_empty:
            while not self.buffer_empty:
                x_loc, y_loc, pressure = self.read_data()
            # Swap touch axis range minimum and maximum if needed
            if self._disp_rotation in {0, 180}:
                if self._touch_flip and self._touch_flip[0]:
                    x_c = (self._calib[0][1], self._calib[0][0])
                else:
                    x_c = (self._calib[0][0], self._calib[0][1])
                if self._touch_flip and self._touch_flip[1]:
                    y_c = (self._calib[1][1], self._calib[1][0])
                else:
                    y_c = (self._calib[1][0], self._calib[1][1])
            if self._disp_rotation in {90, 270}:
                if self._touch_flip[1]:
                    x_c = (self._calib[1][1], self._calib[1][0])
                else:
                    x_c = (self._calib[1][0], self._calib[1][1])
                if self._touch_flip[0]:
                    y_c = (self._calib[0][1], self._calib[0][0])
                else:
                    y_c = (self._calib[0][0], self._calib[0][1])
            # Adjust to calibration range; convert to display size and rotation
            if self._disp_rotation == 0:
                x = int(map_range(y_loc, x_c[0], x_c[1], 0, self._disp_size[0]))
                y = int(map_range(x_loc, y_c[0], y_c[1], 0, self._disp_size[1]))
            elif self._disp_rotation == 90:
                x = int(map_range(x_loc, x_c[0], x_c[1], 0, self._disp_size[0]))
                y = int(map_range(y_loc, y_c[0], y_c[1], self._disp_size[1], 0))
            elif self._disp_rotation == 180:
                x = int(map_range(y_loc, x_c[0], x_c[1], self._disp_size[0], 0))
                y = int(map_range(x_loc, y_c[0], y_c[1], self._disp_size[1], 0))
            elif self._disp_rotation == 270:
                x = int(map_range(x_loc, x_c[0], x_c[1], self._disp_size[0], 0))
                y = int(map_range(y_loc, y_c[0], y_c[1], 0, self._disp_size[1]))
            return (x, y, pressure)
        return None

    def _read_register(self, register: int, length: int) -> bytearray:
        """Low level register reading over I2C, returns a list of values."""
        with self._i2c as i2c:
            i2c.write(bytearray([register & 0xFF]))
            result = bytearray(length)
            i2c.readinto(result)
            # print("$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write_register_byte(self, register: int, value: int) -> None:
        """Low level register writing over I2C, writes one 8-bit value."""
        with self._i2c as i2c:
            i2c.write(bytes([register & 0xFF, value & 0xFF]))
            # print("$%02X <= 0x%02X" % (register, value))


class Adafruit_STMPE610_SPI(Adafruit_STMPE610):
    """SPI interface class for the STMPE610 Resistive Touch sensor.

    :param spi: SPI interface bus
    :param pin cs: touchscreen SPI interface chip select pin
    :param int baudrate: SPI interface clock speed in Hz.
     Defaults to 1000000 (1MHz).
    :param None, (int, int) calibration: touchscreen calibration tuple.
     Defaults to None.
    :param None, (int, int) size: display size tuple (width, height).
     Defaults to None.
    :param int disp_rotation: display rotation in degrees. Values allowed are
     0, 90, 180, and 270. Defaults to 0.
    :param (bool, bool) touch_flip: swap touchscreen axis range minimum and
     maximum values for (x, y) axes as referenced to display 0-degree rotation.
     Defaults to (False, False).

    ** Quickstart: Importing and instantiating Adafruit_STMPE610_I2C**

    Import the Adafruit_STMPE610_SPI class and instantiate for the 2.4" TFT Wing
    after instantiating the display:

    .. code-block:: python

        import adafruit_stmpe610
        ts = adafruit_stmpe610.Adafruit_STMPE610_SPI(spi, cs=cs_pin,
            baudrate=1000000,
            calibration=((357, 3812), (390, 3555)),
            size=(display.width, display.height), disp_rotation=display.rotation,
            touch_flip=(False, False))

    """

    def __init__(
        self,
        spi: SPI,
        cs: Pin,
        baudrate: int = 1000000,
        calibration: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
        size: Optional[Tuple[int, int]] = None,
        disp_rotation: Literal[0, 90, 180, 270] = 0,
        touch_flip: Tuple[bool, bool] = (False, False),
    ) -> None:
        self._calib = calibration
        self._disp_size = size
        self._disp_rotation = disp_rotation
        self._touch_flip = touch_flip

        # Check the touchscreen calibration and display size kwargs.
        if not self._calib:
            self._calib = ((0, 4095), (0, 4095))
        if not self._disp_size:
            self._disp_size = (4095, 4095)

        if self._disp_rotation not in {0, 90, 180, 270}:
            raise ValueError("Display rotation value must be 0, 90, 180, or 270")

        # Check that the STMPE610 was found.
        import adafruit_bus_device.spi_device as spidev

        self._spi = spidev.SPIDevice(spi, cs, baudrate=baudrate)
        # Check device version.
        version = self.get_version
        if _STMPE_VERSION != version:
            # If it fails try SPI MODE 1  -- that is what Arduino does
            self._spi = spidev.SPIDevice(spi, cs, baudrate=baudrate, polarity=0, phase=1)
            version = self.get_version
            if _STMPE_VERSION != version:
                raise RuntimeError(
                    f"Failed to find STMPE610 controller! Chip Version {hex(version).upper()}. "
                    "If you are using the breakout, verify you are in SPI mode."
                )
        super().__init__()

    @property
    def touch_point(
        self,
    ) -> Optional[Tuple[int, int, int]]:
        """Read latest touched point value and convert to calibration-adjusted
        and rotated display coordinates. Commpatible with Displayio Button.
        :return: x, y, pressure
        rtype: int, int, int
        """
        if not self.buffer_empty:
            while not self.buffer_empty:
                x_loc, y_loc, pressure = self.read_data()
            # Swap touch axis range minimum and maximum if needed
            if self._disp_rotation in {0, 180}:
                if self._touch_flip and self._touch_flip[0]:
                    x_c = (self._calib[0][1], self._calib[0][0])
                else:
                    x_c = (self._calib[0][0], self._calib[0][1])
                if self._touch_flip and self._touch_flip[1]:
                    y_c = (self._calib[1][1], self._calib[1][0])
                else:
                    y_c = (self._calib[1][0], self._calib[1][1])
            if self._disp_rotation in {90, 270}:
                if self._touch_flip[1]:
                    x_c = (self._calib[1][1], self._calib[1][0])
                else:
                    x_c = (self._calib[1][0], self._calib[1][1])
                if self._touch_flip[0]:
                    y_c = (self._calib[0][1], self._calib[0][0])
                else:
                    y_c = (self._calib[0][0], self._calib[0][1])
            # Adjust to calibration range; convert to display size and rotation
            if self._disp_rotation == 0:
                x = int(map_range(y_loc, x_c[0], x_c[1], 0, self._disp_size[0]))
                y = int(map_range(x_loc, y_c[0], y_c[1], 0, self._disp_size[1]))
            elif self._disp_rotation == 90:
                x = int(map_range(x_loc, x_c[0], x_c[1], 0, self._disp_size[0]))
                y = int(map_range(y_loc, y_c[0], y_c[1], self._disp_size[1], 0))
            elif self._disp_rotation == 180:
                x = int(map_range(y_loc, x_c[0], x_c[1], self._disp_size[0], 0))
                y = int(map_range(x_loc, y_c[0], y_c[1], self._disp_size[1], 0))
            elif self._disp_rotation == 270:
                x = int(map_range(x_loc, x_c[0], x_c[1], self._disp_size[0], 0))
                y = int(map_range(y_loc, y_c[0], y_c[1], 0, self._disp_size[1]))
            return (x, y, pressure)
        return None

    # Disable should be reconsidered when refactor can be tested.
    def _read_register(self, register: int, length: int) -> bytearray:
        """Low level register reading over SPI, returns a list of values."""
        register = (register | 0x80) & 0xFF  # Read single byte, bit 7 high.
        with self._spi as spi:
            spi.write(bytearray([register]))
            result = bytearray(length)
            spi.readinto(result)
            # print("$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write_register_byte(self, register: int, value: int) -> None:
        """Low level register writing over SPI, writes one 8-bit value."""
        register &= 0x7F  # Write, bit 7 low.
        with self._spi as spi:
            spi.write(bytes([register, value & 0xFF]))
