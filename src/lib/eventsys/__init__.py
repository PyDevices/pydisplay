# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
eventsys — SDL2/PyGame-style input events for *Python.

Quick start::

    import eventsys

    broker = eventsys.Broker()
    keypad = eventsys.KeypadDevice(read=lambda: pressed_keys)
    broker.register(keypad)

    while True:
        for event in broker.poll():
            if event.type == eventsys.QUIT:
                break
"""

from . import keys
from ._broker import Broker, poll_quit_discarding_others
from ._capabilities import capabilities
from ._device import Device, register_device, register_device_class, types
from ._encoder import EncoderDevice
from ._events import events, register_event
from ._joystick import JoystickDevice, JoystickDriver
from ._keypad import KeypadDevice
from ._queue import QueueDevice, VirtualDevices
from ._touch import TouchDevice

register_device_class(types.BROKER, Broker)

Keys = keys.Keys

# Device type constants (also available as eventsys.types.*)
BROKER = types.BROKER
QUEUE = types.QUEUE
TOUCH = types.TOUCH
ENCODER = types.ENCODER
KEYPAD = types.KEYPAD
JOYSTICK = types.JOYSTICK

# Event type constants
QUIT = events.QUIT
KEYDOWN = events.KEYDOWN
KEYUP = events.KEYUP
MOUSEMOTION = events.MOUSEMOTION
MOUSEBUTTONDOWN = events.MOUSEBUTTONDOWN
MOUSEBUTTONUP = events.MOUSEBUTTONUP
MOUSEWHEEL = events.MOUSEWHEEL
JOYAXISMOTION = events.JOYAXISMOTION
JOYBALLMOTION = events.JOYBALLMOTION
JOYHATMOTION = events.JOYHATMOTION
JOYBUTTONDOWN = events.JOYBUTTONDOWN
JOYBUTTONUP = events.JOYBUTTONUP

__all__ = [
    "BROKER",
    "ENCODER",
    "JOYAXISMOTION",
    "JOYBALLMOTION",
    "JOYBUTTONDOWN",
    "JOYBUTTONUP",
    "JOYHATMOTION",
    "JOYSTICK",
    "KEYDOWN",
    "KEYPAD",
    "KEYUP",
    "MOUSEBUTTONDOWN",
    "MOUSEBUTTONUP",
    "MOUSEMOTION",
    "MOUSEWHEEL",
    "QUEUE",
    "QUIT",
    "TOUCH",
    "Broker",
    "Device",
    "EncoderDevice",
    "JoystickDevice",
    "JoystickDriver",
    "Keys",
    "QueueDevice",
    "TouchDevice",
    "VirtualDevices",
    "capabilities",
    "events",
    "poll_quit_discarding_others",
    "register_device",
    "register_event",
    "types",
]
