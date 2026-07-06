# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2025 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_uc8179`
================================================================================

CircuitPython `displayio` driver for UC8179-based ePaper displays

* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

7.5in 800x480 Monochrome eInk / ePaper - Bare Display - UC8179 Chipset: https://www.adafruit.com/product/6396
5.83in 648x480 Monochrome Black / White eInk / ePaper - Bare Display - UC8179 Chipset: https://www.adafruit.com/product/6397
7.5in 800x480 Tri-Color eInk / ePaper - Bare Display: https://www.adafruit.com/product/6415

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's EPaperDisplay library: https://github.com/adafruit/Adafruit_CircuitPython_EPaperDisplay
"""

import displayio

try:
    from epaperdisplay import EPaperDisplay
except ImportError:
    from adafruit_epaperdisplay import EPaperDisplay

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_UC8179.git"

_START_SEQUENCE = (
    b"\x01\x04\x07\x07\x3f\x3f"  # POWERSETTING: VGH=20V, VGL=-20V, VDH=15V, VDL=-15V
    b"\x04\x00"  # POWERON
    b"\x00\x01\x03"  # PANELSETTING
    b"\x61\x04\x00\x00\x00\x00"  # TRES: resolution
    b"\x15\x01\x00"  # DUALSPI: single SPI
    b"\x50\x02\x10\x07"  # WRITE_VCOM
    b"\x60\x01\x22"  # TCON
)

_STOP_SEQUENCE = b"\x02\x00"  # POWEROFF


class UC8179(EPaperDisplay):
    """UC8179 ePaper display driver"""

    def __init__(self, bus, **kwargs):
        width = kwargs.get("width", 800)
        height = kwargs.get("height", 600)

        # Adjust height to be divisible by 8
        width = (width + 7) // 8 * 8

        start_sequence = bytearray(_START_SEQUENCE)
        start_sequence[13] = width >> 8
        start_sequence[14] = width & 0xFF
        start_sequence[15] = height >> 8
        start_sequence[16] = height & 0xFF

        if "highlight_color" in kwargs:
            color_ram_command = 0x13
            black_ram_command = 0x10
            panel_setting = 0x03
        else:
            color_ram_command = None
            black_ram_command = 0x13
            panel_setting = 0x13

        start_sequence[10] = panel_setting

        super().__init__(
            bus,
            start_sequence,
            _STOP_SEQUENCE,
            **kwargs,
            ram_width=800,
            ram_height=600,
            busy_state=False,
            write_black_ram_command=black_ram_command,
            write_color_ram_command=color_ram_command,
            refresh_display_command=0x12,
            refresh_time=16,
            always_toggle_chip_select=True,
        )
