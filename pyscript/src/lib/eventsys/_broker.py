# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Event broker: aggregates devices and dispatches subscribers."""

from ._device import Device, device_class, types
from ._events import events


def poll_quit_discarding_others(broker):
    """One poll pass; True if QUIT was seen. Other events in the batch are discarded."""
    if broker is None:
        return False
    if elist := broker.poll():
        for e in elist:
            if e.type == events.QUIT:
                return True
    return False


class Broker(Device):
    """Polls registered devices and dispatches events to subscribers."""

    type = types.BROKER
    responses = events.filter
    events = events

    def __init__(self):
        super().__init__()
        self.devices = []
        self._device_callbacks = {}
        self._on_quit = None

    def on(self, event_type, callback):
        """Subscribe ``callback`` to one or more event types."""
        if not callable(callback):
            raise ValueError("callback is not callable.")
        if isinstance(event_type, (list, tuple)):
            for et in event_type:
                self.on(et, callback)
            return
        self.subscribe(callback, event_types=[event_type])

    def on_device(self, device_type, callback):
        """Subscribe ``callback`` to all events from devices of ``device_type``."""
        if not callable(callback):
            raise ValueError("callback is not callable.")
        callback_set = self._device_callbacks.get(device_type, set())
        callback_set.add(callback)
        self._device_callbacks[device_type] = callback_set

    def off(self, callback, event_type=None, device_type=None):
        """Unsubscribe ``callback`` from an event type or device type."""
        if device_type is not None:
            if callback_set := self._device_callbacks.get(device_type):
                callback_set.discard(callback)
        elif event_type is not None:
            self.unsubscribe(callback, event_types=[event_type])
        else:
            raise ValueError("set event_type or device_type")

    def subscribe(self, callback, event_types=None, device_types=None):
        """Subscribe to event types (broker-level). Prefer :meth:`on` / :meth:`on_device`."""
        if not callable(callback):
            raise ValueError("callback is not callable.")
        if device_types is not None:
            if event_types is not None:
                raise ValueError("set one of device_types or event_types but not both.")
            for device_type in device_types:
                self.on_device(device_type, callback)
            return
        if event_types is None:
            raise ValueError("event_types is required")
        super().subscribe(callback, event_types)

    def unsubscribe(self, callback, event_types=None, device_types=None):
        if device_types is not None:
            if event_types is not None:
                raise ValueError("set one of device_types or event_types but not both.")
            for device_type in device_types:
                self.off(callback, device_type=device_type)
            return
        if event_types is None:
            raise ValueError("event_types is required")
        super().unsubscribe(callback, event_types)

    def create(self, type=types.QUEUE, **kwargs):
        """Create a device, register it, and return it."""
        cls = device_class(type)
        if cls is None:
            raise ValueError("Invalid device type")
        dev = cls(**kwargs)
        self.register(dev)
        return dev

    def register(self, dev):
        """Register a device to be polled."""
        dev.broker = self
        self.devices.append(dev)

    def unregister(self, dev):
        """Remove a device from polling."""
        if dev in self.devices:
            self.devices.remove(dev)
            dev.broker = None

    def register_quit_cleanup(self, resource, *, before=None, after=None):
        """Wire ``resource.quit()`` to run on ``events.QUIT`` (no process exit)."""
        if not callable(getattr(resource, "quit", None)):
            raise ValueError("resource must have a callable quit() method")

        def _handler():
            try:
                import pydisplay_test_mode

                if pydisplay_test_mode.ENABLED:
                    return
            except ImportError:
                pass
            if before is not None:
                before()
            resource.quit()
            if after is not None:
                after()

        self.on_quit = _handler

    def _handle_quit(self):
        """Invoke the application quit handler without terminating the process."""
        if self._on_quit is not None:
            self._on_quit()

    def quit(self):
        """Run the quit handler (legacy name for :meth:`_handle_quit`)."""
        self._handle_quit()

    @property
    def on_quit(self):
        return self._on_quit

    @on_quit.setter
    def on_quit(self, value):
        if value is not None and not callable(value):
            raise ValueError("on_quit must be callable")
        self._on_quit = value

    def _poll(self):
        try:
            from multimer import needs_pump, pump

            if needs_pump():
                pump()
        except ImportError:
            pass
        eventlist = []
        for device in self.devices:
            dev_events = device.poll()
            if dev_events:
                eventlist.extend(dev_events)
                if callback_list := self._device_callbacks.get(device.type):
                    for func in callback_list:
                        for event in dev_events:
                            func(event)
        return eventlist
