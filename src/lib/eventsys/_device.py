# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Device base class, type registry, and device-type registration."""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


from ._events import events

_mapping = {}


class types:
    """Built-in device type identifiers."""

    UNDEFINED = const(-1)
    BROKER = const(0x00)
    QUEUE = const(0x01)
    TOUCH = const(0x02)
    ENCODER = const(0x03)
    KEYPAD = const(0x04)
    JOYSTICK = const(0x05)


class Device:
    """Base class for input devices."""

    type = types.UNDEFINED
    responses = events.filter

    def __init__(self, read=None, data=None, read2=None, data2=None):
        self._event_callbacks = {}
        self._read = read if read else lambda: None
        self._data = data
        self._read2 = read2 if read2 else lambda: None
        self._data2 = data2
        self._broker = None
        self._state = None
        self._user_data = None

    def poll(self, *args):
        """Poll the device. Always returns a list (possibly empty)."""
        raw = self._poll()
        if raw is None:
            return []
        if not isinstance(raw, list):
            raw = [raw]
        eventlist = [e for e in raw if e.type in events.filter]
        for event in eventlist:
            if event.type == events.QUIT and self._broker is not None:
                self._broker._handle_quit()
            if callback_list := self._event_callbacks.get(event.type):
                for callback in callback_list:
                    callback(event, *args)
        return eventlist

    def subscribe(self, callback, event_types=None):
        event_types = event_types or self.responses
        if not callable(callback):
            raise ValueError("callback is not callable.")
        for event_type in event_types:
            if event_type not in self.responses:
                raise ValueError("the specified event_type is not a response from this device")
            callback_set = self._event_callbacks.get(event_type, set())
            callback_set.add(callback)
            self._event_callbacks[event_type] = callback_set

    def unsubscribe(self, callback, event_types=None):
        event_types = event_types or self.responses
        for event_type in event_types:
            if callback_set := self._event_callbacks.get(event_type):
                callback_set.discard(callback)

    @property
    def broker(self):
        return self._broker

    @broker.setter
    def broker(self, broker):
        self._broker = broker

    @property
    def user_data(self):
        return self._user_data

    @user_data.setter
    def user_data(self, value):
        self._user_data = value


def register_device(type_name, responses):
    """Register a custom device type and return its device class."""
    if not isinstance(type_name, str):
        raise ValueError("type_name must be a string")
    type_name = type_name.strip().upper()
    if not isinstance(responses, list):
        raise ValueError("responses must be a list")
    if not all(isinstance(event, int) for event in responses):
        raise ValueError("all responses must be integers")

    if hasattr(types, type_name):
        raise ValueError(f"Device type {type_name} already exists in types class.")
    class_name = type_name[0].upper() + type_name[1:].lower() + "Device"
    if class_name in [cls.__name__ for cls in _mapping.values()]:
        raise ValueError(f"Device class {class_name} already exists.")

    value = len(_mapping)
    setattr(types, type_name, value)
    new_class = type(class_name, (Device,), {"type": value, "responses": responses})
    _mapping[value] = new_class
    return new_class


def register_device_class(type_id, cls):
    """Register a built-in device class in the type mapping."""
    _mapping[type_id] = cls


def device_class(type_id):
    """Return the device class for a type id."""
    return _mapping.get(type_id)
