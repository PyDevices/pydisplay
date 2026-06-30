# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Touch input device."""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


from ._device import Device, register_device_class, types
from ._events import events

_DEFAULT_TOUCH_ROTATION_TABLE = (0b000, 0b101, 0b110, 0b011)

SWAP_XY = const(0b001)
REVERSE_X = const(0b010)
REVERSE_Y = const(0b100)


class TouchDevice(Device):
    """Touchscreen mapped to mouse button and motion events."""

    type = types.TOUCH
    responses = (events.MOUSEMOTION, events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._data is None:
            raise ValueError("TouchDevice requires a display device as 'data'")
        if self._data2 is None:
            self._data2 = _DEFAULT_TOUCH_ROTATION_TABLE
        self.rotation = self._data.rotation
        self._data.touch_device = self

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = value % 360
        self._mask = self._data2[self._rotation // 90]

    @property
    def rotation_table(self):
        return self._data2

    @rotation_table.setter
    def rotation_table(self, value):
        self._data2 = value

    def _poll(self):
        try:
            touched = self._read()
        except OSError:
            return None
        if touched:
            (x, y, *_) = touched if isinstance(touched[0], int) else touched[0]
            if self._mask & SWAP_XY:
                x, y = y, x
            if self._mask & REVERSE_X:
                x = self._data.width - x - 1
            if self._mask & REVERSE_Y:
                y = self._data.height - y - 1
            last_pos = self._state
            self._state = (x, y)
            if last_pos is not None:
                last_x, last_y = last_pos
                return events.Motion(
                    events.MOUSEMOTION,
                    self._state,
                    (x - last_x, y - last_y),
                    (1, 0, 0),
                    False,
                    None,
                )
            return events.Button(events.MOUSEBUTTONDOWN, self._state, 1, False, None)
        if self._state is not None:
            last_pos = self._state
            self._state = None
            return events.Button(events.MOUSEBUTTONUP, last_pos, 1, False, None)
        return None


register_device_class(types.TOUCH, TouchDevice)
