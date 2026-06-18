# SPDX-License-Identifier: MIT
"""
spibus
"""

import contextlib
import struct

from machine import SPI, Pin
import micropython
from micropython import const

with contextlib.suppress(ImportError):
    from typing import Optional, Union


DC_CMD = const(0)
DC_DATA = const(1)
CS_ACTIVE = const(0)
CS_INACTIVE = const(1)


class SPIBus:
    """
    Represents an SPI bus.

    Args:
        id (int): The ID of the SPI bus.
        baudrate (int): The baudrate of the SPI bus.
        polarity (int): The polarity of the SPI bus.
        phase (int): The phase of the SPI bus.
        bits (int): The number of bits per transfer.
        lsb_first (bool): Whether to send the least significant bit first.
        sck (int): The pin number of the SCK pin.
        mosi (int): The pin number of the MOSI pin.
        miso (int): The pin number of the MISO pin.
        dc (int): The pin number of the DC pin.
        cs (int): The pin number of the CS pin.

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
        sck: int = -1,
        mosi: int = -1,
        miso: int = -1,
        dc: int = -1,
        cs: int = -1,
    ) -> None:
        print("SPIBus loading...")
        if dc == -1:
            raise ValueError("DC pin must be specified")

        self._baudrate: int = baudrate
        self._polarity: int = polarity
        self._phase: int = phase
        self._bits: int = bits
        self._firstbit: int = SPI.LSB if lsb_first else SPI.MSB

        if mosi == -1 and miso == -1 and sck == -1:
            self._spi: SPI = SPI(
                id,
                baudrate=self._baudrate,
                polarity=self._polarity,
                phase=self._phase,
                bits=self._bits,
                firstbit=self._firstbit,
            )
        else:
            self._spi: SPI = SPI(
                id,
                baudrate=self._baudrate,
                polarity=self._polarity,
                phase=self._phase,
                bits=self._bits,
                firstbit=self._firstbit,
                sck=Pin(sck, Pin.OUT),
                mosi=Pin(mosi, Pin.OUT),
                miso=Pin(miso, Pin.IN) if miso > -1 else None,
            )

        # DC and CS pins must be set AFTER the SPI bus is initialized on some boards
        self._dc: Pin = Pin(dc, Pin.OUT, value=DC_DATA)
        self._cs: Union[Pin, callable] = (
            Pin(cs, Pin.OUT, value=CS_INACTIVE) if cs != -1 else lambda val: None
        )

        self._buf1: bytearray = bytearray(1)
        print("SPIBus loaded")

    @micropython.native
    def send(
        self,
        command: Optional[int] = None,
        data: Optional[memoryview] = None,
    ) -> None:
        """
        Sends a command and/or data over the SPI bus.

        Args:
            command (int): The command to send.
            data (memoryview): The data to send.

        Returns:
            None
        """

        self._spi.init(
            baudrate=self._baudrate,
            polarity=self._polarity,
            phase=self._phase,
            bits=self._bits,
            firstbit=self._firstbit,
        )

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
