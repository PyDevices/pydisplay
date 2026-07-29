# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Rotary encoder device."""

from ._device import Device, register_device_class, types
from ._events import events


class EncoderDevice(Device):
    """Encoder wheel and switch mapped to mouse wheel and button events."""

    type = types.ENCODER
    responses = (events.MOUSEWHEEL, events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = (0, False)
        self._data = self._data if self._data else 2

    def _poll(self):
        last_pos, last_pressed = self._state
        pressed = self._read2()
        if pressed != last_pressed:
            self._state = (last_pos, pressed)
            return events.Button(
                events.MOUSEBUTTONDOWN if pressed else events.MOUSEBUTTONUP,
                (0, 0),
                self._data,
                False,
                None,
            )

        pos = self._read()
        if pos != last_pos:
            steps = pos - last_pos
            self._state = (pos, last_pressed)
            if self._data % 2 == 0:
                return events.Wheel(events.MOUSEWHEEL, False, 0, steps, 0, steps, False, None)
            return events.Wheel(events.MOUSEWHEEL, False, steps, 0, steps, 0, False, None)
        return None


register_device_class(types.ENCODER, EncoderDevice)
