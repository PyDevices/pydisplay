# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""MicroPython SPI driver for STMPE610 resistive touch (PiTFT FeatherWing)."""

import time

from machine import Pin

_STMPE_VERSION = 0x0811

_STMPE_SYS_CTRL1 = 0x03
_STMPE_SYS_CTRL1_RESET = 0x02
_STMPE_SYS_CTRL2 = 0x04
_STMPE_TSC_CTRL = 0x40
_STMPE_TSC_CTRL_EN = 0x01
_STMPE_TSC_CTRL_XYZ = 0x00
_STMPE_INT_EN = 0x0A
_STMPE_INT_EN_TOUCHDET = 0x01
_STMPE_ADC_CTRL1 = 0x20
_STMPE_ADC_CTRL2 = 0x21
_STMPE_TSC_CFG = 0x41
_STMPE_FIFO_TH = 0x4A
_STMPE_FIFO_SIZE = 0x4C
_STMPE_FIFO_STA = 0x4B
_STMPE_FIFO_STA_RESET = 0x01
_STMPE_FIFO_STA_EMPTY = 0x20
_STMPE_TSC_I_DRIVE = 0x58
_STMPE_INT_STA = 0x0B
_STMPE_INT_CTRL = 0x09


def _map_range(x, in_min, in_max, out_min, out_max):
    in_range = in_max - in_min
    if in_range:
        mapped = (x - in_min) / in_range
    else:
        mapped = 0.5
    mapped *= out_max - out_min
    mapped += out_min
    return int(max(min(mapped, out_max), out_min) if out_min <= out_max else min(max(mapped, out_max), out_min))


class STMPE610:
    """STMPE610 on a dedicated SPI chip-select."""

    def __init__(self, spi, cs, *, width=240, height=320, rotation=0, calibration=None):
        self._spi = spi
        self._cs = Pin(cs, Pin.OUT, value=1)
        self._width = width
        self._height = height
        self._rotation = rotation
        self._calib = calibration if calibration is not None else ((0, 4095), (0, 4095))
        version = self._get_version()
        if version != _STMPE_VERSION:
            self._spi.init(polarity=0, phase=1)
            version = self._get_version()
            if version != _STMPE_VERSION:
                raise RuntimeError(f"STMPE610 not found (version 0x{version:04X})")
        self._init_chip()

    def _write_byte(self, register, value):
        self._cs(0)
        self._spi.write(bytes([register & 0x7F, value & 0xFF]))
        self._cs(1)

    def _read_bytes(self, register, length):
        buf = bytearray(length)
        self._cs(0)
        self._spi.write(bytes([register | 0x80]))
        self._spi.readinto(buf)
        self._cs(1)
        return buf

    def _read_byte(self, register):
        return self._read_bytes(register, 1)[0]

    def _get_version(self):
        return (self._read_byte(0) << 8) | self._read_byte(1)

    def _init_chip(self):
        self._write_byte(_STMPE_SYS_CTRL1, _STMPE_SYS_CTRL1_RESET)
        time.sleep_ms(1)
        self._write_byte(_STMPE_SYS_CTRL2, 0)
        self._write_byte(_STMPE_TSC_CTRL, _STMPE_TSC_CTRL_XYZ | _STMPE_TSC_CTRL_EN)
        self._write_byte(_STMPE_INT_EN, _STMPE_INT_EN_TOUCHDET)
        self._write_byte(_STMPE_ADC_CTRL1, 0x60)
        self._write_byte(_STMPE_ADC_CTRL2, 0x02)
        self._write_byte(_STMPE_TSC_CFG, 0xC0 | 0x20 | 0x04)
        self._write_byte(0x56, 0x06)
        self._write_byte(_STMPE_FIFO_TH, 1)
        self._write_byte(_STMPE_FIFO_STA, _STMPE_FIFO_STA_RESET)
        self._write_byte(_STMPE_FIFO_STA, 0)
        self._write_byte(_STMPE_TSC_I_DRIVE, 0x01)
        self._write_byte(_STMPE_INT_STA, 0xFF)
        self._write_byte(_STMPE_INT_CTRL, 0x05)

    @property
    def touched(self):
        return (self._read_byte(_STMPE_TSC_CTRL) & 0x80) == 0x80

    @property
    def buffer_empty(self):
        return (self._read_byte(_STMPE_FIFO_STA) & _STMPE_FIFO_STA_EMPTY) != 0

    def _read_raw(self):
        d1 = self._read_byte(0xD7)
        d2 = self._read_byte(0xD7)
        d3 = self._read_byte(0xD7)
        d4 = self._read_byte(0xD7)
        x_loc = (d1 << 4) | (d2 >> 4)
        y_loc = ((d2 & 0x0F) << 8) | d3
        if self.buffer_empty:
            self._write_byte(_STMPE_INT_STA, 0xFF)
        return x_loc, y_loc, d4

    @property
    def touch_point(self):
        if not self.touched:
            return None
        x_loc, y_loc, _pressure = self._read_raw()
        x_c = self._calib[0]
        y_c = self._calib[1]
        if self._rotation == 0:
            x = _map_range(y_loc, x_c[0], x_c[1], 0, self._width)
            y = _map_range(x_loc, y_c[0], y_c[1], 0, self._height)
        elif self._rotation == 90:
            x = _map_range(x_loc, x_c[0], x_c[1], 0, self._width)
            y = _map_range(y_loc, y_c[0], y_c[1], self._height, 0)
        elif self._rotation == 180:
            x = _map_range(y_loc, x_c[0], x_c[1], self._width, 0)
            y = _map_range(x_loc, y_c[0], y_c[1], self._height, 0)
        else:
            x = _map_range(x_loc, x_c[0], x_c[1], self._width, 0)
            y = _map_range(y_loc, y_c[0], y_c[1], 0, self._height)
        return (x, y)
