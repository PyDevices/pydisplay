# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
epaperdisplay_chip — MicroPython shim for CircuitPython ``epaperdisplay.EPaperDisplay``.

Chip drivers (``ssd1680``, ``acep7in``, etc.) subclass this on MicroPython.
On CircuitPython the firmware builtin ``epaperdisplay`` module is used instead.
"""

try:
    from time import sleep_ms
except ImportError:
    from time import sleep

    def sleep_ms(ms):
        sleep(ms / 1000)

_DELAY = 0x80


def _refresh_sequence_bytes(refresh_display_command):
    if isinstance(refresh_display_command, int):
        return bytes([refresh_display_command, 0x00])
    return refresh_display_command


def _send_command_sequence(bus, sequence, two_byte_sequence_length=False, wait_busy=None, busy_state=True):
    i = 0
    n = len(sequence)
    while i < n:
        cmd = sequence[i]
        meta = sequence[i + 1]
        delay = bool(meta & _DELAY)
        data_size = meta & ~_DELAY
        data_offset = i + 2
        if two_byte_sequence_length:
            data_size = (data_size << 8) | sequence[i + 2]
            data_offset = i + 3
        params = sequence[data_offset : data_offset + data_size]
        delay_ms = 0
        if delay:
            delay_index = data_offset + data_size
            if delay_index < n:
                delay_ms = sequence[delay_index]
                if delay_ms == 255:
                    delay_ms = 500
        bus.send(cmd, params)
        if delay_ms:
            sleep_ms(delay_ms)
        if wait_busy is not None:
            while wait_busy() == busy_state:
                pass
        i = data_offset + data_size + (1 if delay else 0)


class EPaperDisplay:
    """Minimal CircuitPython-compatible e-paper chip driver base."""

    def __init__(self, bus, start_sequence, stop_sequence=b"", **kwargs):
        self.bus = bus
        self.width = kwargs["width"]
        self.height = kwargs["height"]
        self.colstart = kwargs.get("colstart", 0)
        self.rowstart = kwargs.get("rowstart", 0)
        self.rotation = kwargs.get("rotation", 0)
        self.write_black_ram_command = kwargs["write_black_ram_command"]
        self.black_bits_inverted = kwargs.get("black_bits_inverted", False)
        self.write_color_ram_command = kwargs.get("write_color_ram_command")
        self.set_column_window_command = kwargs.get("set_column_window_command")
        self.set_row_window_command = kwargs.get("set_row_window_command")
        self.set_current_column_command = kwargs.get("set_current_column_command")
        self.set_current_row_command = kwargs.get("set_current_row_command")
        self.address_little_endian = kwargs.get("address_little_endian", False)
        self.two_byte_sequence_length = kwargs.get("two_byte_sequence_length", False)
        self.busy_state = kwargs.get("busy_state", True)
        self.refresh_time = int(kwargs.get("refresh_time", 40) * 1000)
        self.start_up_time = int(kwargs.get("start_up_time", 0) * 1000)
        self._stop_sequence = stop_sequence
        self._refresh_sequence = _refresh_sequence_bytes(kwargs.get("refresh_display_command", 0))
        self._busy_pin = kwargs.get("busy_pin")

        reset_fn = getattr(bus, "reset", None)
        if reset_fn is not None:
            try:
                reset_fn()
            except (RuntimeError, OSError, TypeError):
                pass
        if self.start_up_time:
            sleep_ms(self.start_up_time)
        _send_command_sequence(
            bus,
            start_sequence,
            two_byte_sequence_length=self.two_byte_sequence_length,
            wait_busy=self._busy_read,
            busy_state=self.busy_state,
        )

    def _busy_read(self):
        if self._busy_pin is None:
            return not self.busy_state
        pin = self._busy_pin
        if hasattr(pin, "value"):
            if callable(pin.value):
                return pin.value()
            return pin.value
        return pin

    def refresh(self):
        _send_command_sequence(
            self.bus,
            self._refresh_sequence,
            two_byte_sequence_length=self.two_byte_sequence_length,
        )
        if self._busy_pin is None:
            sleep_ms(self.refresh_time)
        else:
            while self._busy_read() == self.busy_state:
                pass
