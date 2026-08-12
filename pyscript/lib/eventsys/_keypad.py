# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Keypad device."""

import events
import keys

from ._device import Device, register_device_class, types


def _key_name(key):
    """Human-readable name for a key code (never assume ``chr``-safe)."""
    name = keys.keyname(key)
    if name != "Unknown":
        return name
    if isinstance(key, int) and 32 <= key <= 126:
        return chr(key)
    return "0x%x" % key if isinstance(key, int) else str(key)


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
            return events.Key(events.KEYUP, _key_name(key), key, 0, 0, None)
        pressed = keys - self._state
        if pressed:
            key = pressed.pop()
            self._state.add(key)
            return events.Key(events.KEYDOWN, _key_name(key), key, 0, 0, None)
        return None


register_device_class(types.KEYPAD, KeypadDevice)
