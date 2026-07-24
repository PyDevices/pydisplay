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

    type = types.POINTER
    responses = (events.MOUSEMOTION, events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP)

    def __init__(
        self, *args, read=None, data=None, data2=None, display=None, rotation_table=None, **kwargs
    ):
        read = read if read is not None else (args[0] if args else None)
        data = display if display is not None else data
        data2 = rotation_table if rotation_table is not None else data2
        super().__init__(read=read, data=data, data2=data2, **kwargs)
        if self._data is None:
            raise ValueError("TouchDevice requires display=")
        if self._data2 is None:
            self._data2 = _DEFAULT_TOUCH_ROTATION_TABLE
        self.rotation = self._data.rotation
        self._data.touch_device = self
        # Synthetic samples in *display* coordinates (rotation already applied).
        # Each entry is ``(x, y)`` (finger down) or ``None`` (finger up).
        self._inject_q = []

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

    def inject_clear(self):
        """Drop pending synthetic samples (does not emit an up)."""
        self._inject_q = []

    def inject_point(self, xy):
        """Queue one sample: ``(x, y)`` display coords, or ``None`` for up."""
        self._inject_q.append(xy)

    def inject_tap(self, x, y, hold_frames=1):
        """Queue a press/release at display coordinates.

        One down sample + one up is enough for LVGL CLICKED / hit-layer
        PRESSED. Extra hold frames each need an indev poll and dominated
        automation timing on slow MCU debug builds.
        """
        pt = (int(x), int(y))
        self._inject_q.append(pt)
        # Optional extra downs only if explicitly requested (>1).
        n = max(1, int(hold_frames))
        for _ in range(n - 1):
            self._inject_q.append(pt)
        self._inject_q.append(None)

    def _poll(self):
        if self._inject_q:
            sample = self._inject_q.pop(0)
            if sample is not None:
                x, y = int(sample[0]), int(sample[1])
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


register_device_class(types.POINTER, TouchDevice)
