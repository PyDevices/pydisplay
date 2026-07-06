# SPDX-FileCopyrightText: Copyright (c) 2026 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ssd1677`
================================================================================

CircuitPython `displayio` driver for SSD1677-based ePaper displays


* Author(s): Liz Clark

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""


try:
    import typing

    from fourwire import FourWire
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1677.git"

_START_SEQUENCE = (
    b"\x12\x80\x00\x14"  # soft reset, wait 20ms
    b"\x18\x00\x01\x80"  # temperature sensor control (internal)
    b"\x0c\x00\x05\xae\xc7\xc3\xc0\x40"  # booster soft start
    b"\x01\x00\x03\xdf\x01\x02"  # driver output control: 480 gates, GD=0, SM=1, TB=0
    b"\x11\x00\x01\x01"  # data entry mode: X inc, Y dec
    b"\x3c\x00\x01\x01"  # border waveform control
    # Set RAM X window: 0 to 799 (pixel addressing, little-endian 2 bytes each)
    b"\x44\x00\x04\x00\x00\x1f\x03"
    # Set RAM Y window: 479 down to 0 (reversed for Y-decrement mode)
    b"\x45\x00\x04\xdf\x01\x00\x00"
    # Set RAM X counter to 0
    b"\x4e\x00\x02\x00\x00"
    # Set RAM Y counter to 479
    b"\x4f\x00\x02\xdf\x01"
    # Auto write BW RAM (clear to white), wait busy
    b"\x46\x80\x01\xf7\xff"
    # Auto write RED RAM (clear to white), wait busy
    b"\x47\x80\x01\xf7\xff"
    # Display update control 1: bypass RED as 0
    b"\x21\x00\x02\x40\x00"
    # Display update control 2: full refresh with OTP LUT
    b"\x22\x00\x01\xf7"
)

_STOP_SEQUENCE = (
    b"\x22\x00\x01\x83"  # power off sequence
    b"\x20\x00\x00"  # activation
    b"\x10\x00\x01\x01"  # deep sleep
)

_REFRESH_SEQUENCE = b"\x20\x00\x00"  # activation


class SSD1677(EPaperDisplay):
    r"""SSD1677 driver

    :param bus: The data bus the display is on
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *width* (``int``) --
          Display width
        * *height* (``int``) --
          Display height
        * *rotation* (``int``) --
          Display rotation
    """

    def __init__(self, bus: FourWire, **kwargs) -> None:
        stop_sequence = bytearray(_STOP_SEQUENCE)
        try:
            bus.reset()
        except RuntimeError:
            # No reset pin defined, so no deep sleeping
            stop_sequence = b""

        start_sequence = bytearray(_START_SEQUENCE)

        width = kwargs.get("width", 800)
        height = kwargs.get("height", 480)

        # Patch driver output control: MUX = height - 1
        mux = height - 1
        start_sequence[19] = mux & 0xFF
        start_sequence[20] = (mux >> 8) & 0xFF

        # Patch RAM X window end (pixels): offsets 35,36
        x_end = width - 1
        start_sequence[35] = x_end & 0xFF
        start_sequence[36] = (x_end >> 8) & 0xFF

        # Patch RAM Y window start (= height-1, Y decrements): offsets 40,41
        y_start = height - 1
        start_sequence[40] = y_start & 0xFF
        start_sequence[41] = (y_start >> 8) & 0xFF

        # Patch RAM Y counter initial value: offsets 52,53
        start_sequence[52] = y_start & 0xFF
        start_sequence[53] = (y_start >> 8) & 0xFF

        super().__init__(
            bus,
            start_sequence,
            stop_sequence,
            **kwargs,
            ram_width=800,
            ram_height=480,
            busy_state=True,
            write_black_ram_command=0x24,
            black_bits_inverted=False,
            refresh_display_command=_REFRESH_SEQUENCE,
            refresh_time=1.6,
            seconds_per_frame=5.0,
            grayscale=False,
            two_byte_sequence_length=True,
            address_little_endian=True,
        )
