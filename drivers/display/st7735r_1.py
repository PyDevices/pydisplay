# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

from busdisplay import BusDisplay

_INIT_SEQUENCE = [
    (0x36, b"\x70", 0),
    (0x3A, b"\x05", 0),
    (0xB1, b"\x01\x2c\x2d", 0),
    (0xB2, b"\x01\x2c\x2d", 0),
    (0xB3, b"\x01\x2c\x2d\x01\x2c\x2d", 0),
    (0xB4, b"\x07", 0),
    (0xC0, b"\xa2\x02\x84", 0),
    (0xC1, b"\xc5", 0),
    (0xC2, b"\x0a\x00", 0),
    (0xC3, b"\x8a\x2a", 0),
    (0xC4, b"\x8a\xee", 0),
    (0xC5, b"\x0e", 0),
    (0xE0, b"\x0f\x1a\x0f\x18\x2f\x28\x20\x22\x1f\x1b\x23\x37\x00\x07\x02\x10", 0),
    (0xE1, b"\x0f\x1b\x0f\x17\x33\x2c\x29\x2e\x30\x30\x39\x3f\x00\x07\x03\x10", 0),
    (0xF0, b"\x01", 0),
    (0xF6, b"\x00", 0),
    (0x11, None, 255),
    (0x29, None, 255),
]


class ST7735R(BusDisplay):
    def __init__(self, bus, **kwargs):
        super().__init__(bus, _INIT_SEQUENCE, **kwargs)
