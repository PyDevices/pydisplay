# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Keypad device."""

from ._device import Device, register_device_class, types
from ._events import events


class KeypadDevice(Device):
    """Keypad or keyboard mapped to KEYDOWN/KEYUP events."""

    type = types.KEYPAD
    responses = (events.KEYDOWN, events.KEYUP)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = set()

    def _poll(self):
        keys = set(self._read())
        released = self._state - keys
        if released:
            key = released.pop()
            self._state.remove(key)
            return events.Key(events.KEYUP, chr(key), key, 0, 0, None)
        pressed = keys - self._state
        if pressed:
            key = pressed.pop()
            self._state.add(key)
            return events.Key(events.KEYDOWN, chr(key), key, 0, 0, None)
        return None


register_device_class(types.KEYPAD, KeypadDevice)
