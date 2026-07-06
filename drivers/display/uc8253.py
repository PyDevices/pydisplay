# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2025 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_uc8253`
================================================================================

CircuitPython `displayio` driver for UC8253-based ePaper displays

* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* `3.7" 416x240 Monochrome Black/White eInk / ePaper - Bare Display - UC8253 Chipset <https://www.adafruit.com/product/6395>`_
* `3.7" 416x240 Tri-Color Red / Black / White eInk - Bare Display - UC8253 Chipset <https://www.adafruit.com/product/6394>`_

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

_START_SEQUENCE = (
    b"\x04\x00"  # POWERON
    b"\x50\x01\xd7"  # VCOM/CDI
    b"\x00\x02\xcf\x8d"  # PANELSETTING: 0b11001111, 0x8D
)

_STOP_SEQUENCE = b"\x02\x00"  # POWEROFF

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_UC8253.git"


class UC8253(EPaperDisplay):
    """UC8253 ePaper display driver"""

    def __init__(self, bus, vcom_cdi=0xD7, **kwargs):
        start_sequence = bytearray(_START_SEQUENCE)

        if "highlight_color" in kwargs:
            color_ram_command = 0x13
            black_ram_command = 0x10
            panel_setting = 0b11001111
        else:
            color_ram_command = None
            black_ram_command = 0x13
            panel_setting = 0b11011111

        start_sequence[4] = vcom_cdi
        start_sequence[7] = panel_setting

        super().__init__(
            bus,
            start_sequence,
            _STOP_SEQUENCE,
            **kwargs,
            ram_width=240,
            ram_height=480,
            busy_state=True,
            write_black_ram_command=black_ram_command,
            write_color_ram_command=color_ram_command,
            refresh_display_command=0x12,
            refresh_time=16,
            always_toggle_chip_select=True,
        )
