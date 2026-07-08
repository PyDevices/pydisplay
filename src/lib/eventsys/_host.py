# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Host event device and LVGL virtual device fan-out."""

from ._device import Device, register_device_class, types
from ._events import events
from .keys import chord_matches


class HostEventsDevice(Device):
    """Returns multiple event types from a native host event pump callback."""

    type = types.HOST
    responses = events.filter

    def __init__(
        self,
        read=None,
        data=None,
        data2=None,
        *,
        host_read=None,
        display=None,
        event_filter=None,
    ):
        read = host_read if host_read is not None else read
        data = display if display is not None else data
        data2 = event_filter if event_filter is not None else data2
        super().__init__(read=read, data=data, data2=data2)
        if self._data2 is None:
            self._data2 = events.filter
        if hasattr(self._data, "touch_scale"):
            self.scale = self._data.touch_scale
        else:
            self.scale = 1
        self._quit_chord_ok = hasattr(self._data, "quit_chord")

    def _poll(self):
        if (dev_events := self._read()) is not None:
            eventlist = []
            quit_chord = self._data.quit_chord if self._quit_chord_ok else None
            chord_key = quit_chord[0] if quit_chord else None
            for event in dev_events:
                if quit_chord:
                    if event.type == events.KEYDOWN and chord_matches(
                        quit_chord, event.key, event.mod
                    ):
                        event = events.Quit(events.QUIT)
                    elif event.type == events.KEYUP and event.key == chord_key:
                        continue
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
    """Fan-out host events into virtual touch/encoder/keypad devices for LVGL."""

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
            self._virtual_devices.poll_host_device()
            event = self._fifo.pop(0) if self._fifo else None
            if self._callback is not None:
                self._callback(event, *args)

        def add_event(self, event):
            self._fifo.append(event)

    def __init__(self, host_device):
        self._host_device = host_device
        self._vd_touch = self.VirtualDevice(self, types.TOUCH)
        self._vd_encoder = self.VirtualDevice(self, types.ENCODER)
        self._vd_keypad = self.VirtualDevice(self, types.KEYPAD)
        self.devices = [self._vd_touch, self._vd_encoder, self._vd_keypad]

    def poll_host_device(self):
        for e in self._host_device.poll():
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


register_device_class(types.HOST, HostEventsDevice)
