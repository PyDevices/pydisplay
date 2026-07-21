# SPDX-FileCopyrightText: 2026 Brad Barnett / PyDevices
#
# SPDX-License-Identifier: MIT
"""CH422G I2C IO expander (Waveshare ESP32-S3 RGB boards, etc.).

Register "addresses" are separate 7-bit I2C slave addresses (the chip's
``i2c_address`` constructor arg is unused / ignored by silicon). Protocol
matches ``esp-arduino-libs/ESP32_IO_Expander`` ``esp_io_expander_ch422g``.
"""

from machine import Pin
from micropython import const

# Fixed CH422G command/register slave addresses (byte-addr >> 1).
_WR_SET = const(0x24)  # 0x48 >> 1 — direction / OE / OD
_WR_OC = const(0x23)  # 0x46 >> 1 — OC0..OC3 outputs
_WR_IO = const(0x38)  # 0x70 >> 1 — IO0..IO7 outputs
_RD_IO = const(0x26)  # 0x4D >> 1 — IO0..IO7 inputs

_IO_OE = const(1 << 0)
_OD_EN = const(1 << 2)


class CH422G:
    """Minimal CH422G driver with PCA9554-style ``Pin`` helpers."""

    OUT = Pin.OUT
    IN = Pin.IN

    def __init__(self, i2c, address=0x20):
        # ``address`` kept for API parity with other expanders; CH422G ignores it.
        self.i2c = i2c
        self.address = address
        self._wr_set = 0x01  # IO_OE default on
        self._wr_oc = 0x0F
        self._wr_io = 0xFF
        self.enable_all_io_output()
        self._write_outputs()

    def _writeto(self, addr, value):
        self.i2c.writeto(addr, bytes((value & 0xFF,)))

    def enable_all_io_output(self):
        self._wr_set = (self._wr_set | _IO_OE) & ~_OD_EN
        self._writeto(_WR_SET, self._wr_set)

    def enable_all_io_input(self):
        self._wr_set &= ~_IO_OE
        self._writeto(_WR_SET, self._wr_set)

    def _write_outputs(self):
        self._writeto(_WR_OC, self._wr_oc)
        self._writeto(_WR_IO, self._wr_io)

    def digital_write(self, pin, value):
        if pin < 0 or pin > 11:
            raise ValueError("pin must be 0..11 (IO0-7, OC0-3)")
        level = 1 if value else 0
        if pin < 8:
            mask = 1 << pin
            self._wr_io = (self._wr_io | mask) if level else (self._wr_io & ~mask)
            self._writeto(_WR_IO, self._wr_io)
        else:
            bit = pin - 8
            mask = 1 << bit
            self._wr_oc = (self._wr_oc | mask) if level else (self._wr_oc & ~mask)
            self._writeto(_WR_OC, self._wr_oc)

    def digital_read(self, pin):
        if pin < 0 or pin > 7:
            raise ValueError("digital_read supports IO0..IO7 only")
        raw = self.i2c.readfrom(_RD_IO, 1)[0]
        return (raw >> pin) & 1

    def Pin(self, pin, mode=Pin.OUT, value=None):
        return _CH422GPin(self, pin, mode, value)


class _CH422GPin:
    def __init__(self, chip, pin, mode, value):
        self._chip = chip
        self._pin = pin
        if mode == Pin.OUT:
            chip.enable_all_io_output()
            if value is not None:
                chip.digital_write(pin, value)
        elif mode == Pin.IN:
            chip.enable_all_io_input()
        else:
            raise ValueError("mode must be Pin.OUT or Pin.IN")

    def value(self, v=None):
        if v is None:
            return self._chip.digital_read(self._pin)
        self._chip.digital_write(self._pin, v)
        return None

    def __call__(self, v=None):
        return self.value(v)
