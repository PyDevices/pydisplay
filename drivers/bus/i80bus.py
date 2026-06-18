# SPDX-FileCopyrightText: 2023 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
i80bus
"""

from array import array
import contextlib
import struct

import micropython
from micropython import const
from uctypes import addressof

with contextlib.suppress(ImportError):
    from typing import Optional

# _I80BaseBus will work with either Pin class, but I80Bus will only work with GPIO_Pin
try:
    from gpio_pin import GPIO_Pin as Pin
except ImportError:
    from machine import Pin

if 0:
    ptr8 = ptr16 = ptr32 = None  # For type hints


DC_CMD = const(0)
DC_DATA = const(1)
CS_ACTIVE = const(0)
CS_INACTIVE = const(1)
WR_ACTIVE = const(1)
WR_INACTIVE = const(0)


class _I80BaseBus:
    """
    Base class for I80 bus communication.

    Args:
        dc (int): The pin number for the data/command control.
        cs (int): The pin number for the chip select.
        wr (int): The pin number for the write control.
        data (list[int]): A list of pin numbers for the data pins.
        freq (int): The frequency for the bus. Defaults to 20,000,000.
    """

    def __init__(
        self,
        dc: int,
        cs: int,
        wr: int,
        data: list[int],
        freq: int = 20_000_000,
    ) -> None:
        print("I80Bus loading...")
        # Not used in this class; may be used in subclasses like _i80bus_rp2.py
        self._freq = freq

        # Create a list of Pin objects for the data pins
        # NOTE:  data8-15 are optional and not implemented in most subclasses
        data_pins = [Pin(pin, Pin.OUT) for pin in data]

        # Setup the control pins
        # _wr_active, _wr_inactive are boolean values
        # indicating the level of the pin in that state.  True is high, False is low.
        self._dc: Pin = Pin(dc, Pin.OUT)
        self._dc(DC_CMD)  # Set the DC pin to the command level

        # If cs was not specified, set it to a lambda that does nothing
        # so lines like the next won't fail.
        self._cs: Pin = Pin(cs, Pin.OUT) if cs != -1 else lambda val: None
        self._cs(CS_INACTIVE)  # Set the CS pin to the inactive level

        self._wr: Pin = Pin(wr, Pin.OUT)
        self._wr(WR_INACTIVE)  # Set the WR pin to the inactive level

        self._buf1: bytearray = bytearray(1)

        self._setup(data_pins)
        print("I80Bus loaded")

    @micropython.native
    def send(self, command: Optional[int] = None, data: Optional[memoryview] = None) -> None:
        """
        Sends a command and/or data to the device.
        Args:
            command (Optional[int]): The command to send. Defaults to None.
            data (Optional[memoryview]): The data to send. Defaults to None.
        Returns:
            None
        """

        self._cs(CS_ACTIVE)

        if command is not None:
            struct.pack_into("B", self._buf1, 0, command)
            self._dc(DC_CMD)
            self._write(self._buf1, 1)

        if data and len(data):
            self._dc(DC_DATA)
            self._write(data, len(data))

        self._cs(CS_INACTIVE)

    def deinit(self):
        pass

    def __del__(self):
        self.deinit()


class I80Bus(_I80BaseBus):
    """
    Class for I80 bus communication.

    Args:
        dc (int): The pin number for the data/command control.
        cs (int): The pin number for the chip select.
        wr (int): The pin number for the write control.
        data (list[int]): A list of pin numbers for the data pins.
        freq (int): The frequency for the bus. Defaults to 20,000,000.
    """

    def _setup(self, data_pins: list[Pin]) -> None:
        # Make sure GPIO_Pin was imported
        if not hasattr(Pin, "BSRR"):
            raise ValueError("GPIO_Pin not imported")

        # If self._is_32bit is True the _write method will use a 32-bit set and a 32-bit
        # clear register.  Otherwise, the _write method will use set_reset registers
        # which use the lower 16 bits for set and the upper 16 bits for clear.
        self._is_32bit = self._wr.BSRR is None

        # Both lut mode and sequential mode need the write pin registers and masks saved to use in viper.
        # Subclasses may not need the write pin registers and masks, so they are defined here instead of
        # in __init__.   Subclasses should override _setup.
        if self._is_32bit:
            self._wr_mask = self._wr_not_mask = 1 << self._wr.pin()
            self._wr_reg = self._wr.gpio() + (self._wr.SET if WR_ACTIVE else self._wr.CLR)
            self._wr_not_reg = self._wr.gpio() + (self._wr.CLR if WR_ACTIVE else self._wr.SET)
        else:
            self._wr_reg = self._wr_not_reg = self._wr.gpio() + self._wr.BSRR
            self._wr_mask = 1 << (self._wr.pin() + (0 if WR_ACTIVE else 16))
            self._wr_not_mask = 1 << (self._wr.pin() + (16 if WR_ACTIVE else 0))

        if False:  # Set to True to print the write pin registers and masks
            print(
                f"\n{self._wr=}\n    {self._wr_reg=:#010x}, {self._wr_mask=:#034b}\n    {self._wr_not_reg=:#010x}, {self._wr_not_mask=:#034b}\n"
            )

        # Determine which mode, lut or sequential, to use
        # If all pins are on the same port and sequential:
        if all(p.port() == data_pins[0].port() for p in data_pins) and all(
            data_pins[i].pin() + 1 == data_pins[i + 1].pin() for i in range(len(data_pins) - 1)
        ):
            # Use sequential mode
            self._setup_seq(data_pins)
        else:
            # Use LUT mode
            self._setup_lut(data_pins)

    def _setup_lut(self, pins: list[Pin]) -> None:
        """
        Setup lookup tables, pin data and the _write method for LUT mode.
        """
        print("Using LUT mode")
        if len(pins) != 8:
            raise ValueError("LUT mode only supports 8 data pins")
        self._write = self._write_lut

        # Setup the data for pin_data and the lookup tables
        lut_len = 2 ** len(pins)  # Number of entries per lut -- 256 for 8-bit bus width
        port_list = []  # list of port numbers in use
        for item in [p.port() for p in pins]:  # Create a list of unique port numbers
            if item not in port_list:
                port_list.append(item)
        # Map port numbers to lookup table index
        lut_map = {port: i for i, port in enumerate(port_list)}
        self._num_luts = len(lut_map)  # Number of lookup tables
        self._lookup_tables = [None] * self._num_luts  # list of bytearray lookup tables
        pin_masks = [None] * self._num_luts  # list of 32-bit pin masks
        regsA = [None] * self._num_luts  # list of SET registers if _is_32bit else BSRR registers
        regsB = [None] * self._num_luts  # list of CLR registers if _is_32bit else unused

        # Create the pin_masks, populate the 2 reg lists and initialize the lookup_tables
        # for each port of 16 or 32 pins.  Will be saved in array pin_data later.
        for i in range(self._num_luts):
            port = port_list[i]
            port_pins = [p for p in pins if p.port() == port]
            first_pin = port_pins[0]
            pin_mask = sum([1 << p.pin() for p in port_pins])
            if self._is_32bit:
                self._lookup_tables[i] = array("I", [0] * lut_len)  # 32-bit array
                regsA[i] = first_pin.gpio() + first_pin.SET
                regsB[i] = first_pin.gpio() + first_pin.CLR
            else:
                self._lookup_tables[i] = array("H", [0] * lut_len)  # 16-bit array
                regsA[i] = first_pin.gpio() + first_pin.BSRR
                regsB[i] = 0x0
            pin_masks[i] = pin_mask
            if False:  # Set to True to print the pin data
                print(f"    {i=}: {port=}, A={regsA[i]:#0x}, B={regsB[i]:#0x}, ", end="")
                print(f"mask={pin_masks[i]:#034b}, pins={[p.pin() for p in port_pins]}")

        # Populate the lookup tables
        for index in range(lut_len):  # Iterate through all possible 8-bit values (0 to 255)
            for bit_number, pin in enumerate(pins):  # Iterate through each pin
                if index & (1 << bit_number):  # If the bit is set in the index
                    # Get the current value for index from the appropriate lookup table
                    value = self._lookup_tables[lut_map[pin.port()]][index]
                    value |= 1 << pin.pin()  # Update the value for the pin
                    self._lookup_tables[lut_map[pin.port()]][index] = value  # Save the value

        # Save all settings in a struct-like array pin_data for use in viper.
        # Could be merged with the first loop above, but left here for clarity.
        pin_data = array("I", [0] * 4 * self._num_luts)
        for i in range(self._num_luts):
            pin_data[i * 4 + 0] = pin_masks[i]
            pin_data[i * 4 + 1] = regsA[i]
            pin_data[i * 4 + 2] = regsB[i]
            pin_data[i * 4 + 3] = addressof(self._lookup_tables[i])

            if False:  # Set to True to print the lookup tables
                print(
                    f"\nlut={i}: mask={pin_masks[i]:#034b}, {regsA[i]=:#010x}, {regsB[i]=:#010x}"
                )
                for j in range(lut_len):
                    print(f"       {j:3d}: {self._lookup_tables[i][j]:#034b}")

        self._pin_data = memoryview(pin_data)  # Save a memoryview into pin_data for use in viper

    @micropython.viper
    def _write_lut(self, data: ptr8, length: int):
        # Cache these values to avoid accessing the self namespace every iteration
        wr_not_reg = ptr32(self._wr_not_reg)
        wr_not_mask = int(self._wr_not_mask)
        wr_reg = ptr32(self._wr_reg)
        wr_mask = int(self._wr_mask)
        is_32bit = bool(self._is_32bit)  # noqa: F841
        pin_data = ptr32(self._pin_data)
        num_luts = int(self._num_luts)

        last: int = -1
        for i in range(length):  # Iterate through the data
            wr_not_reg[0] = wr_not_mask  # WR Inactive
            val = data[i]  # Get the value from the data
            # If the pin states need to be changed (optimization for colors where LSB == MSB, like white and black)
            if val != last:
                if False:
                    print(f"{val=:#010b} ({val=:#04x})")  # noqa: E701
                for n in range(num_luts):  # Iterate through the lookup tables
                    if False:
                        print(f"{    n=}")  # noqa: E701
                    pin_mask = pin_data[n * 4 + 0]  # Get the pin mask
                    regA = ptr32(pin_data[n * 4 + 1])  # Get the SET or BSRR register
                    if True:  # Should be `if is_32bit:` but not supported in viper
                        regB = ptr32(pin_data[n * 4 + 2])  # Only need regB (CLEAR) for 32-bit
                        lut = ptr32(pin_data[n * 4 + 3])  # 32-bit lookup table
                        tx_value: int = lut[val]  # Get the 32-bit value from the lookup table
                        regA[0] = tx_value  # Set the bits that are on
                        regB[0] = tx_value ^ pin_mask  # Clear the bits that are off
                    else:
                        lut = ptr16(pin_data[n * 4 + 3])  # 16-bit lookup table
                        tx_value: int = lut[val]  # Get the 16-bit value from the lookup table
                        # Set the bits that are on and clear the bits that are off
                        regA[0] = (tx_value << 0) | ((tx_value ^ pin_mask) << 16)
                    if False:  # Print debug info
                        print(f"        {tx_value=:#034b}")
                        print(f"        {pin_mask=:#034b}")
                        print(
                            f"          wrote: {(tx_value | ((tx_value ^ pin_mask) << 16)):#034b}"
                        )
                #                 raise ValueError("Debugging")
                last = val  # Save the value for the next iteration
            wr_reg[0] = wr_mask  # WR Active

    def _setup_seq(self, pins: list[Pin]) -> None:
        print("Using sequential mode")
        if len(pins) == 8:
            self._write = self._write_seq8
        elif len(pins) == 16:
            self._write = self._write_seq16
        else:
            raise ValueError("Sequential mode only supports 8 or 16 data pins")

        # Setup the data for pin_data
        pin_mask = sum([1 << p.pin() for p in pins])
        first_pin = pins[0]
        if self._is_32bit:
            regA = first_pin.gpio() + first_pin.SET
            regB = first_pin.gpio() + first_pin.CLR
        else:
            regA = first_pin.gpio() + first_pin.BSRR
            regB = 0x0
        shift = first_pin.pin()

        # save all settings in an array pin_data for use in viper
        pin_data = array("I", [0] * 4)
        pin_data[0] = pin_mask
        pin_data[1] = regA
        pin_data[2] = regB
        pin_data[3] = shift
        self._pin_data = memoryview(pin_data)

    @micropython.viper
    def _write_seq8(self, data: ptr8, length: int):
        # Cache these values to avoid accessing the self namespace every iteration
        wr_not_reg = ptr32(self._wr_not_reg)
        wr_not_mask = int(self._wr_not_mask)
        wr_reg = ptr32(self._wr_reg)
        wr_mask = int(self._wr_mask)
        is_32bit = bool(self._is_32bit)
        pin_data = ptr32(self._pin_data)

        pin_mask = pin_data[0]
        regA = ptr32(pin_data[1])
        regB = ptr32(pin_data[2])
        shift = pin_data[3]

        last: int = -1
        for i in range(length):  # Iterate through the data
            wr_not_reg[0] = wr_not_mask  # WR Inactive
            val = data[i]  # Get the value from the data
            # If the pin states need to be changed (optimization for colors where LSB == MSB, like white and black)
            if val != last:
                tx_value: int = val << shift  # Shift the value to the correct position
                if is_32bit:
                    regA[0] = tx_value  # Set the bits that are on
                    regB[0] = tx_value ^ pin_mask  # Clear the bits that are off
                else:
                    # Set the bits that are on and clear the bits that are off
                    regA[0] = tx_value | ((tx_value ^ pin_mask) << 16)
                last = val  # Save the value for the next iteration
            wr_reg[0] = wr_mask  # WR Active

    @micropython.viper
    def _write_seq16(self, data: ptr16, length: int):
        raise NotImplementedError("16 pin sequential mode not implemented")
