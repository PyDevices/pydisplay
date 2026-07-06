# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ssd1680`
================================================================================

CircuitPython `displayio` driver for SSD1680-based ePaper displays


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit 2.13" Tri-Color eInk Display Breakout <https://www.adafruit.com/product/4947>`_
* `Adafruit 2.13" Tri-Color eInk Display FeatherWing <https://www.adafruit.com/product/4814>`_
* `Adafruit 2.13" Mono eInk Display FeatherWing <https://www.adafruit.com/product/4195>`_


**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import time

import digitalio

try:
    import typing

    from fourwire import FourWire
except ImportError:
    pass


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1680.git"

_START_SEQUENCE = (
    b"\x12\x80\x00\x14"  # soft reset and wait 20ms
    b"\x11\x00\x01\x03"  # Ram data entry mode
    b"\x3c\x00\x01\x03"  # border color
    b"\x2c\x00\x01\x36"  # Set vcom voltage
    b"\x03\x00\x01\x17"  # Set gate voltage
    b"\x04\x00\x03\x41\xae\x32"  # Set source voltage
    b"\x4e\x00\x01\x01"  # ram x count
    b"\x4f\x00\x02\x00\x00"  # ram y count
    b"\x01\x00\x03\x00\x00\x00"  # set display size
)

_DISPLAY_UPDATE_MODE = b"\x22\x00\x01\xf4"  # display update mode

_STOP_SEQUENCE = b"\x10\x80\x01\x01\x64"  # Deep Sleep


# LUT for original MagTag panel: FPC-A005 (SSD1680, User ID first byte 0x00)
FPC_A005_LUT = (
    b"\x2a\x60\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L0
    b"\x20\x60\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L1
    b"\x28\x60\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L2
    b"\x00\x60\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L3
    b"\x00\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L4
    b"\x00\x02\x00\x05\x14\x00\x00"  # TP, SR, RP Group0
    b"\x1e\x1e\x00\x00\x00\x00\x01"  # TP, SR, RP Group1
    b"\x00\x02\x00\x05\x14\x00\x00"  # TP, SR, RP Group2
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group3
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group4
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group5
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group6
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group7
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group8
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group9
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group10
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group11
    b"\x24\x22\x22\x22\x23\x32\x00\x00\x00"  # FR, XON
)

# LUT for FPC-7519rev.b and newer panels (User ID first byte != 0x00).
# GxEPD2_4G (GDEM029T94) waveform with L0/L3 swapped to match CircuitPython's luma mapping
# (luma 0→L0=black, luma 255→L3=white) and 0x48 flag for DC-balanced drive.
FPC7519_LUT = (
    b"\x20\x48\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L0 (black)
    b"\x08\x48\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L1 (dark gray)
    b"\x02\x48\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L2 (light gray)
    b"\x40\x48\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L3 (white)
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L4 (VCOM)
    b"\x0a\x19\x00\x03\x08\x00\x00"  # TP, SR, RP Group0
    b"\x14\x01\x00\x14\x01\x00\x03"  # TP, SR, RP Group1
    b"\x0a\x03\x00\x08\x19\x00\x00"  # TP, SR, RP Group2
    b"\x01\x00\x00\x00\x00\x00\x01"  # TP, SR, RP Group3
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group4
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group5
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group6
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group7
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group8
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group9
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group10
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group11
    b"\x22\x22\x22\x22\x22\x22\x00\x00\x00"  # FR, XON
)


_SSD1683_START_SEQUENCE = (
    b"\x12\x80\x00\xc8"  # SW_RESET + 200ms delay (cold-boot charge-pump settle)
    b"\x0c\x00\x04\x8b\x9c\xa4\x0f"  # BOOST_SOFTSTART
    b"\x11\x00\x01\x03"  # RAM data entry mode
    b"\x3c\x00\x01\x03"  # border
    b"\x21\x00\x02\x00\x00"  # DISP_CTRL1 (no source-line shift)
    b"\x3f\x00\x01\x07"  # END_OPTION
    b"\x03\x00\x01\x17"  # gate voltage
    b"\x04\x00\x03\x41\xa8\x32"  # source voltage
    b"\x2c\x00\x01\x30"  # VCOM (default 0x30, offset 41)
    b"\x4e\x00\x01\x00"  # RAM X count
    b"\x4f\x00\x02\x00\x00"  # RAM Y count
    b"\x01\x00\x03\x00\x00\x00"  # driver output control (gate lo/hi at offsets 54/55)
)

_SSD1683_DISPLAY_UPDATE_MODE = b"\x22\x00\x01\xcf"  # 4-gray LUT-based update

# 4-gray waveform LUT for GDEY042T81 / FPC-190 — native GxEPD2 order (unswapped).
# Correct level order relies on the BW/Color RAM banks being swapped in __init__
# (write_black_ram_command=0x26, write_color_ram_command=0x24).
SSD1683_GRAY4_LUT = bytes.fromhex(
    # 5 waveform groups x 6 phase-rows (7 B each); GxEPD2 GDEY042T81 lut_4G[0:210]
    "010A1B0F030101"  # group 0
    "050A010A010101"
    "05080302040101"
    "01040402000101"
    "01000000000101"
    "01000000000101"
    "010A1B0F030101"  # group 1
    "054A018A010101"
    "05480382840101"
    "01848482000101"
    "01000000000101"
    "01000000000101"
    "010A1B8F030101"  # group 2
    "054A018A010101"
    "05488382040101"
    "01040402000101"
    "01000000000101"
    "01000000000101"
    "018A1B8F030101"  # group 3
    "054A018A010101"
    "05488302040101"
    "01040402000101"
    "01000000000101"
    "01000000000101"
    "018A9B8F030101"  # group 4
    "054A018A010101"
    "05480342040101"
    "01040442000101"
    "01000000000101"
    "01000000000101"
    "00000000000000"  # 2 reserved phase-rows
    "00000000000000"
    "020000"  # frame-rate / repeat tail
)  # 227 bytes — GDEY042T81 / FPC-190 (matches Adafruit_EPD ssd1683.py)


def detect_ssd1680_panel(data_pin, clk_pin, cs_pin, dc_pin, rst_pin):
    """Read SSD1680 User ID (register 0x2E) via half-duplex bitbang SPI.

    Must be called before the SPI bus is initialized (FourWire claims the pins).
    The SSD1680 responds on the MOSI/DATA line in half-duplex mode, not MISO.

    Returns first byte of User ID:
      0x00        -> FPC-A005 (original/legacy MagTag panel)
      anything else -> FPC-7519rev.b or newer panel; use FPC7519_LUT
    """
    data = digitalio.DigitalInOut(data_pin)
    clk = digitalio.DigitalInOut(clk_pin)
    cs = digitalio.DigitalInOut(cs_pin)
    dc = digitalio.DigitalInOut(dc_pin)
    rst = digitalio.DigitalInOut(rst_pin)

    for pin in (data, clk, cs, dc, rst):
        pin.direction = digitalio.Direction.OUTPUT
        pin.value = False

    rst.value = False
    time.sleep(0.001)
    rst.value = True
    time.sleep(0.010)

    cmd = 0x2E
    for i in range(8):
        data.value = bool(cmd & (1 << (7 - i)))
        clk.value = True
        clk.value = False

    data.switch_to_input(pull=digitalio.Pull.UP)
    dc.value = True

    result = 0
    for _ in range(8):
        result = (result << 1) | (1 if data.value else 0)
        clk.value = True
        clk.value = False

    cs.value = True

    for pin in (data, clk, cs, dc, rst):
        pin.deinit()

    return result


# pylint: disable=too-few-public-methods
class SSD1680(EPaperDisplay):
    r"""SSD1680 driver

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
        * *vcom* (``int``) --
          Set vcom voltage register value
        * *vsh2* (``int``) --
          Set vsh2 voltage register value
        * *custom_lut* (``bytes``) --
          Custom look-up table settings
    """

    def __init__(
        self, bus: FourWire, vcom: int = 0x36, vsh2: int = 0x00, custom_lut: bytes = b"", **kwargs
    ) -> None:
        if "colstart" not in kwargs:
            kwargs["colstart"] = 8
        stop_sequence = bytearray(_STOP_SEQUENCE)
        try:
            bus.reset()
        except RuntimeError:
            # No reset pin defined, so no deep sleeping
            stop_sequence = b""
        load_lut = b""
        enable_color_ram = b""
        display_update_mode = bytearray(_DISPLAY_UPDATE_MODE)
        if custom_lut:
            load_lut = b"\x32" + len(custom_lut).to_bytes(2) + custom_lut
            display_update_mode[-1] = 0xC7
            if kwargs.get("grayscale", False):
                # Enable COLOR RAM as second source (required for 4-gray mode)
                enable_color_ram = b"\x21\x00\x02\x00\x80"

        start_sequence = bytearray(
            _START_SEQUENCE + enable_color_ram + load_lut + display_update_mode
        )
        start_sequence[15] = vcom

        start_sequence[24] = vsh2

        width = kwargs["width"]
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 90:
            width, height = height, width
        start_sequence[38] = (width - 1) & 0xFF
        start_sequence[39] = ((width - 1) >> 8) & 0xFF

        super().__init__(
            bus,
            start_sequence,
            stop_sequence,
            **kwargs,
            ram_width=250,
            ram_height=296,
            busy_state=True,
            write_black_ram_command=0x24,
            write_color_ram_command=0x26,
            set_column_window_command=0x44,
            set_row_window_command=0x45,
            set_current_column_command=0x4E,
            set_current_row_command=0x4F,
            refresh_display_command=0x20,
            always_toggle_chip_select=False,
            address_little_endian=True,
            two_byte_sequence_length=True,
        )


# pylint: disable=too-few-public-methods
class SSD1683(EPaperDisplay):
    r"""SSD1683 driver for 4-gray grayscale e-paper displays.

    Designed for the 4.2" 400×300 GDEY042T81 panel (#6381, FPC-190 ribbon).
    Gate lines run along the height dimension (300), so DRIVER_CONTROL is set
    from height rather than width.

    :param bus: The data bus the display is on
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *width* (``int``) --
          Display width (400 for the 4.2" panel)
        * *height* (``int``) --
          Display height (300 for the 4.2" panel)
        * *rotation* (``int``) --
          Display rotation
        * *vcom* (``int``) --
          VCOM voltage register value (default 0x30)
        * *custom_lut* (``bytes``) --
          Custom waveform LUT; pass ``SSD1683_GRAY4_LUT`` for 4-gray mode
    """

    def __init__(self, bus: FourWire, vcom: int = 0x30, custom_lut: bytes = b"", **kwargs) -> None:
        kwargs["grayscale"] = True  # SSD1683 always runs in 4-gray mode
        if "colstart" not in kwargs:
            kwargs["colstart"] = 0
        stop_sequence = bytearray(_STOP_SEQUENCE)
        try:
            bus.reset()
            # Cold-boot settle: after a true power-on, the controller's regulators
            # need time before the start sequence loads the LUT (mirrors the
            # framebuffer driver's sleep(0.1)+busy_wait). A short delay here plus the
            # longer SW_RESET delay below prevents a corrupt-LUT speckle on cold boot.
            time.sleep(0.2)
        except RuntimeError:
            stop_sequence = b""
        load_lut = b""
        display_update_mode = bytearray(_SSD1683_DISPLAY_UPDATE_MODE)
        if custom_lut:
            load_lut = b"\x32" + len(custom_lut).to_bytes(2) + custom_lut

        start_sequence = bytearray(_SSD1683_START_SEQUENCE + load_lut + display_update_mode)
        start_sequence[41] = vcom

        width = kwargs["width"]
        height = kwargs["height"]
        # Save gate count before any rotation swap — always the physical height (300)
        gate_height = height
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 90:
            width, height = height, width
        start_sequence[54] = (gate_height - 1) & 0xFF
        start_sequence[55] = ((gate_height - 1) >> 8) & 0xFF

        super().__init__(
            bus,
            start_sequence,
            stop_sequence,
            **kwargs,
            ram_width=255,  # <256 forces 1-byte X (0x44) addressing; SSD168x X is byte-addressed
            ram_height=300,
            busy_state=True,
            write_black_ram_command=0x26,  # swapped vs SSD1680: displayio packs luma
            write_color_ram_command=0x24,  # bit7->black,bit6->color; SSD1683 wants the opposite
            set_column_window_command=0x44,
            set_row_window_command=0x45,
            set_current_column_command=0x4E,
            set_current_row_command=0x4F,
            refresh_display_command=0x20,
            always_toggle_chip_select=False,
            address_little_endian=True,
            two_byte_sequence_length=True,
        )
