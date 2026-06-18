# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
An I80 bus driver for the RP2 using a PIO state machine.
"""

import struct

from machine import Pin
import micropython
from rp2 import PIO, StateMachine, asm_pio

from . import I80Bus as _I80Bus
from . import Optional

# workaround Ruff errors for PIO statements
if 0:
    wrap_target = 0
    pull = 0
    block = 0
    out = 0
    pins = 0
    not_osre = 0
    irq = 0
    wrap = 0
    rel = 0
    ifempty = 0
    label = 0
    jmp = 0


class I80Bus(_I80Bus):
    """
    I80Bus for the RP2 using a PIO State Machine.
    """

    def __init__(self, *args, **kwargs) -> None:
        print("Using _i80bus_rp2.py")
        super().__init__(*args, **kwargs)

    @asm_pio(
        out_init=[PIO.OUT_LOW] * 8,
        sideset_init=PIO.OUT_LOW,
        out_shiftdir=0,
        autopull=True,
        pull_thresh=8,
    )
    def _i80bus_pio() -> None:
        """
        PIO state machine for the I80 bus.
        """
        # set the state machine to the initial state
        wrap_target()
        pull(ifempty, block).side(0)  # Wait for the fifo to become non-empty
        label("out8")
        out(pins, 8).side(1)  # Output the next 8 bits in the fifo and strobe the WR pin
        jmp(not_osre, "out8").side(0)  # If the fifo is empty, continue
        irq(rel(0)).side(0)  # Tell the main process the transfer is complete
        wrap()

    def setup(self, pins: list[int], wr: int, freq: int) -> None:
        """
        Configure the rp2 PIO and state machines to drive the data bus and control lines.
        """
        # verify there are exactly 8 pins
        if len(pins) != 8:
            raise ValueError("There must be exactly 8 data pins.")
        # verify that the pins are consecutive
        if not all(pins[i] + 1 == pins[i + 1] for i in range(len(pins) - 1)):
            raise ValueError("The pins must be consecutive.")

        # create the state machine
        prog_cycles = 4  #  4 clock cycles per iteration
        self._sm = StateMachine(
            0,
            self._i80bus_pio,
            freq=freq * prog_cycles,
            out_base=Pin(pins[0]),
            sideset_base=self.wr,
        )
        self._sm.irq(None)
        self._sm.exec("set(x, 0)")
        self._sm.exec("set(y, 0)")
        self._sm.active(1)

    @micropython.native
    def tx_color(
        self,
        cmd: int,
        data: memoryview,
        x_start: int,
        y_start: int,
        x_end: int,
        y_end: int,
    ) -> None:
        """
        Transmit color data over the bus.
        """
        while self.trans_done:  # Wait for the previous transaction to finish.
            pass

        self.trans_done = False

        self.cs(self._cs_active)

        struct.pack_into("B", self.buf1, 0, cmd)
        self.dc(self._dc_cmd)
        self._write(self.buf1, 1)

        if data and len(data):
            self.dc(self._dc_data)
            self._write(data, len(data))

    @micropython.native
    def tx_param(self, cmd: int, data: Optional[memoryview] = None) -> None:
        """
        Transmit parameters over the bus.
        """
        self.cs(self._cs_active)

        struct.pack_into("B", self.buf1, 0, cmd)
        self.dc(self._dc_cmd)
        self._write(self.buf1, 1)

        if data and len(data):
            self.dc(self._dc_data)
            self._write(data, len(data))

        self.cs(self._cs_inactive)

    @micropython.native
    def _tx_color_done_irq(self) -> None:
        """
        Callback function to be called when a color transaction is done.
        """
        self.cs(self._cs_inactive)
        self.tx_color_done_cb()

    @micropython.native
    def _write(self, data: memoryview, length: int) -> None:
        """
        Write the data to the display.
        """
        self._sm.put(data)
        while self._sm.tx_fifo():  # Wait for the fifo to become empty.
            pass
