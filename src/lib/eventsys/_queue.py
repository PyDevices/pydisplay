# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Queue device and LVGL virtual device fan-out."""

from ._device import Device, register_device_class, types
from ._events import events


class QueueDevice(Device):
    """Returns multiple event types from a native poll callback."""

    type = types.QUEUE
    responses = events.filter

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._data2 is None:
            self._data2 = events.filter
        if hasattr(self._data, "touch_scale"):
            self.scale = self._data.touch_scale
        else:
            self.scale = 1

    def _poll(self):
        if (dev_events := self._read()) is not None:
            eventlist = []
            for event in dev_events:
                if event.type in self._data2:
                    if (
                        event.type
                        in (
                            events.MOUSEMOTION,
                            events.MOUSEBUTTONDOWN,
                            events.MOUSEBUTTONUP,
                        )
                        and (scale := self.scale) != 1
                    ):
                        pos = (int(event.pos[0] // scale), int(event.pos[1] // scale))
                        if event.type == events.MOUSEMOTION:
                            rel = (event.rel[0] // scale, event.rel[1] // scale)
                            event = events.Motion(
                                event.type,
                                pos,
                                rel,
                                event.buttons,
                                event.touch,
                                event.window,
                            )
                        else:
                            event = events.Button(
                                event.type,
                                pos,
                                event.button,
                                event.touch,
                                event.window,
                            )
                    eventlist.append(event)
            return eventlist if eventlist else None
        return None


class VirtualDevices:
    """Fan-out queue events into virtual touch/encoder/keypad devices for LVGL."""

    class VirtualDevice:
        def __init__(self, virtual_devices, device_type):
            self._virtual_devices = virtual_devices
            self.type = device_type
            self.user_data = None
            self._fifo = []
            self._callback = None

        def subscribe(self, callback):
            self._callback = callback

        def poll(self, *args):
            self._virtual_devices.poll_queue_device()
            event = self._fifo.pop(0) if self._fifo else None
            if self._callback is not None:
                self._callback(event, *args)

        def add_event(self, event):
            self._fifo.append(event)

    def __init__(self, queue_device):
        self._queue_device = queue_device
        self._vd_touch = self.VirtualDevice(self, types.TOUCH)
        self._vd_encoder = self.VirtualDevice(self, types.ENCODER)
        self._vd_keypad = self.VirtualDevice(self, types.KEYPAD)
        self.devices = [self._vd_touch, self._vd_encoder, self._vd_keypad]

    def poll_queue_device(self):
        for e in self._queue_device.poll():
            if (
                e.type == events.MOUSEBUTTONDOWN
                or e.type == events.MOUSEBUTTONUP
                or (e.type == events.MOUSEMOTION and e.buttons[0])
            ):
                self._vd_touch.add_event(e)
            elif e.type == events.MOUSEWHEEL:
                self._vd_encoder.add_event(e)
            elif e.type == events.KEYDOWN or e.type == events.KEYUP:
                self._vd_keypad.add_event(e)


register_device_class(types.QUEUE, QueueDevice)
