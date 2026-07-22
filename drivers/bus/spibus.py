# SPDX-License-Identifier: MIT
"""
spibus
"""

import struct
import sys
from time import sleep_ms

from machine import SPI, Pin

try:
    from machine import SoftSPI
except ImportError:  # pragma: no cover
    SoftSPI = None  # type: ignore[assignment, misc]

import micropython
from micropython import const

DC_CMD = const(0)
DC_DATA = const(1)
CS_ACTIVE = const(0)
CS_INACTIVE = const(1)


def _pin_unset(pin) -> bool:
    """True when a pin kwarg was omitted (None / -1 sentinel)."""
    return pin is None or pin == -1


class SPIBus:
    """
    Represents an SPI bus.

    Args:
        id (int): The ID of the SPI bus (ignored when ``soft=True``).
        baudrate (int): The baudrate of the SPI bus.
        polarity (int): The polarity of the SPI bus.
        phase (int): The phase of the SPI bus.
        bits (int): The number of bits per transfer (hardware SPI).
        lsb_first (bool): Whether to send the least significant bit first.
        soft (bool): Use ``machine.SoftSPI`` (bitbang). Requires sck/mosi.
        sck: SCK pin (int, name str, or Pin); omit/-1 for default SPI pins.
        mosi: MOSI pin (int, name str, or Pin); omit/-1 for default SPI pins.
        miso: MISO pin (int, name str, or Pin); omit/-1 for default/none.
        dc: DC pin (int, name str, or Pin); required.
        cs: CS pin (int, name str, or Pin); omit/-1 for no CS.

    Raises:
        ValueError: If the DC pin is not specified.
    """

    def __init__(
        self,
        *,
        id: int = 2,
        baudrate: int = 24_000_000,
        polarity: int = 0,
        phase: int = 0,
        bits: int = 8,
        lsb_first: bool = False,
        soft: bool = False,
        sck: int = -1,
        mosi: int = -1,
        miso: int = -1,
        dc: int = -1,
        cs: int = -1,
        reset: int = -1,
    ) -> None:
        print("SPIBus loading...")
        if _pin_unset(dc):
            raise ValueError("DC pin must be specified")

        self._baudrate: int = baudrate
        self._polarity: int = polarity
        self._phase: int = phase
        self._bits: int = bits
        self._soft: bool = soft
        spi_cls = SoftSPI if soft else SPI
        if soft and SoftSPI is None:
            raise RuntimeError("machine.SoftSPI not available")
        self._firstbit: int = spi_cls.LSB if lsb_first else spi_cls.MSB

        if soft:
            if _pin_unset(sck) or _pin_unset(mosi):
                raise ValueError("soft SPI requires sck and mosi")
            self._sck = Pin(sck, Pin.OUT)
            self._mosi = Pin(mosi, Pin.OUT)
            self._miso = None if _pin_unset(miso) else Pin(miso, Pin.IN)
            soft_kw = {
                "baudrate": self._baudrate,
                "polarity": self._polarity,
                "phase": self._phase,
                "sck": self._sck,
                "mosi": self._mosi,
            }
            if self._miso is not None:
                soft_kw["miso"] = self._miso
            # firstbit is optional on some ports
            try:
                self._spi = SoftSPI(firstbit=self._firstbit, **soft_kw)
            except TypeError:
                self._spi = SoftSPI(**soft_kw)
        elif _pin_unset(mosi) and _pin_unset(miso) and _pin_unset(sck):
            self._sck = None
            self._mosi = None
            self._miso = None
            self._spi: SPI = SPI(
                id,
                baudrate=self._baudrate,
                polarity=self._polarity,
                phase=self._phase,
                bits=self._bits,
                firstbit=self._firstbit,
            )
        else:
            self._sck = Pin(sck, Pin.OUT)
            self._mosi = Pin(mosi, Pin.OUT)
            self._miso = None if _pin_unset(miso) else Pin(miso, Pin.IN)
            self._spi: SPI = SPI(
                id,
                baudrate=self._baudrate,
                polarity=self._polarity,
                phase=self._phase,
                bits=self._bits,
                firstbit=self._firstbit,
                sck=self._sck,
                mosi=self._mosi,
                miso=self._miso,
            )

        # DC and CS pins must be set AFTER the SPI bus is initialized on some boards
        self._dc: Pin = Pin(dc, Pin.OUT, value=DC_DATA)
        self._cs = Pin(cs, Pin.OUT, value=CS_INACTIVE) if not _pin_unset(cs) else lambda val: None
        self._reset = None if _pin_unset(reset) else Pin(reset, Pin.OUT, value=1)

        self._buf1: bytearray = bytearray(1)
        print("SPIBus loaded")

    def reset(self) -> None:
        """Hardware reset pulse when ``reset`` pin was provided."""
        if self._reset is None:
            raise RuntimeError("No reset pin defined")
        self._reset.value(0)
        sleep_ms(10)
        self._reset.value(1)
        sleep_ms(10)

    @micropython.native
    def send(
        self,
        command=None,
        data=None,
    ) -> None:
        """
        Sends a command and/or data over the SPI bus.

        Args:
            command (int): The command to send.
            data (memoryview): The data to send.

        Returns:
            None
        """

        # SoftSPI: reinit every transfer corrupts window/pixel streams.
        if self._soft:
            pass
        else:
            # Re-pass pins only on ESP hardware SPI: SPI.init(baudrate=...) without
            # sck/mosi clears the GPIO matrix there. rp2 rejects pin kwargs.
            init_kw = {
                "baudrate": self._baudrate,
                "polarity": self._polarity,
                "phase": self._phase,
                "bits": self._bits,
                "firstbit": self._firstbit,
            }
            if self._sck is not None and sys.platform.startswith("esp"):
                init_kw["sck"] = self._sck
                init_kw["mosi"] = self._mosi
                init_kw["miso"] = self._miso
            self._spi.init(**init_kw)

        self._cs(CS_ACTIVE)

        if command is not None:
            struct.pack_into("B", self._buf1, 0, command)
            self._dc(DC_CMD)
            self._spi.write(self._buf1)

        if data and len(data):
            self._dc(DC_DATA)
            self._spi.write(data)

        self._cs(CS_INACTIVE)

    def deinit(self) -> None:
        """
        Deinitializes the SPI bus.

        Returns:
            None
        """

        self._spi.deinit()

    def __del__(self) -> None:
        self.deinit()
