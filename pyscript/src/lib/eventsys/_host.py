# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Host event device and LVGL virtual device fan-out."""

from ._device import Device, register_device_class, types
from ._events import events
from .keys import Keys, key_triggers_quit


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
                if event.type == events.KEYDOWN:
                    # Quit chord (default Ctrl+Q) and Android / TV Back → QUIT.
                    # Why K_AC_BACK: Android SDL maps KEYCODE_BACK here; PyScript
                    # TV browsers map BrowserBack/GoBack/Back to the same code.
                    if key_triggers_quit(event.type, event.key, event.mod, quit_chord):
                        event = events.Quit(events.QUIT)
                elif event.type == events.KEYUP:
                    # Swallow key-up for quit keys so apps do not see a dangling
                    # KEYUP after the KEYDOWN was converted to QUIT.
                    if event.key == Keys.K_AC_BACK:
                        continue
                    if quit_chord and event.key == chord_key:
                        continue
                if event.type in self._data2:
                    if event.type in (
                        events.MOUSEMOTION,
                        events.MOUSEBUTTONDOWN,
                        events.MOUSEBUTTONUP,
                    ):
                        # Prefer live display.touch_scale (PGDisplay window scale).
                        # Finger events are already panel-normalized in sdldisplay.
                        scale = getattr(self._data, "touch_scale", None)
                        if scale is None:
                            scale = self.scale
                        else:
                            self.scale = scale
                        if scale and scale != 1:
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
    """Fan-out host events into virtual pointer/encoder/keypad devices for LVGL."""

    class VirtualDevice:
        def __init__(self, virtual_devices, device_type):
            self._virtual_devices = virtual_devices
            self.type = device_type
            self.user_data = None
            self._fifo = []
            self._callback = None
            # Multipoint snapshot for LVGL gestures (SDL fingers / etc.).
            self.points = ()
            self._fingers = {}  # finger_id -> (x, y)

        def subscribe(self, callback):
            self._callback = callback

        def poll(self, *args):
            self._virtual_devices.poll_host_device()
            event = self._fifo.pop(0) if self._fifo else None
            if self._callback is not None:
                self._callback(event, *args)

        def add_event(self, event):
            self._fifo.append(event)

        def _set_finger(self, finger_id, xy):
            if xy is None:
                self._fingers.pop(finger_id, None)
            else:
                self._fingers[finger_id] = xy
            self.points = tuple((pos[0], pos[1], fid) for fid, pos in self._fingers.items())

    def __init__(self, host_device):
        self._host_device = host_device
        self._vd_pointer = self.VirtualDevice(self, types.POINTER)
        self._vd_encoder = self.VirtualDevice(self, types.ENCODER)
        self._vd_keypad = self.VirtualDevice(self, types.KEYPAD)
        self.devices = [self._vd_pointer, self._vd_encoder, self._vd_keypad]

    def poll_host_device(self):
        for e in self._host_device.poll():
            if e.type in (events.FINGERDOWN, events.FINGERMOTION):
                self._vd_pointer._set_finger(e.finger_id, e.pos)
                # Primary-finger mouse synth for existing POINTER path / clicks.
                # Prefer the lowest finger id as primary.
                if self._vd_pointer._fingers:
                    primary_id = min(self._vd_pointer._fingers)
                    px, py = self._vd_pointer._fingers[primary_id]
                    if e.finger_id == primary_id:
                        if e.type == events.FINGERDOWN:
                            self._vd_pointer.add_event(
                                events.Button(events.MOUSEBUTTONDOWN, (px, py), 1, True, e.window)
                            )
                        else:
                            self._vd_pointer.add_event(
                                events.Motion(
                                    events.MOUSEMOTION,
                                    (px, py),
                                    (0, 0),
                                    (1, 0, 0),
                                    True,
                                    e.window,
                                )
                            )
            elif e.type == events.FINGERUP:
                was_primary = self._vd_pointer._fingers and e.finger_id == min(
                    self._vd_pointer._fingers
                )
                last = self._vd_pointer._fingers.get(e.finger_id, e.pos)
                self._vd_pointer._set_finger(e.finger_id, None)
                if was_primary:
                    self._vd_pointer.add_event(
                        events.Button(events.MOUSEBUTTONUP, last, 1, True, e.window)
                    )
            elif (
                e.type == events.MOUSEBUTTONDOWN
                or e.type == events.MOUSEBUTTONUP
                or (e.type == events.MOUSEMOTION and e.buttons[0])
            ):
                # Ignore OS touch→mouse synth when we already track fingers.
                if getattr(e, "touch", False) and self._vd_pointer._fingers:
                    continue
                self._vd_pointer.add_event(e)
            elif e.type == events.MOUSEWHEEL:
                self._vd_encoder.add_event(e)
            elif e.type == events.KEYDOWN or e.type == events.KEYUP:
                self._vd_keypad.add_event(e)


register_device_class(types.HOST, HostEventsDevice)
