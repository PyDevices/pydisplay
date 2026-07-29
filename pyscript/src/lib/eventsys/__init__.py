# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
eventsys — SDL2/PyGame-style input events for *Python.

Quick start::

    import eventsys

    runtime = eventsys.Runtime()
    keypad = eventsys.KeypadDevice(read=lambda: pressed_keys)
    runtime.register(keypad)

    while True:
        for event in runtime.poll():
            if event.type == eventsys.QUIT:
                break

Optional mappers (import explicitly; not loaded by ``import eventsys``)::

    from eventsys.touch_keypad import TouchKeypad
    from eventsys.joystick_keys import JoystickKeys
"""

from . import keys
from ._capabilities import capabilities
from ._device import Device, register_device, register_device_class, types
from ._encoder import EncoderDevice
from ._events import events, register_event
from ._host import HostEventsDevice, VirtualDevices
from ._joystick import JoystickDevice, JoystickDriver
from ._keypad import KeypadDevice
from ._runtime import DEFAULT_REFRESH_MS, Runtime
from ._touch import TouchDevice

Keys = keys.Keys
default_quit_chord = keys.default_quit_chord
key_triggers_quit = keys.key_triggers_quit
chord_matches = keys.chord_matches

# Device type constants (also available as eventsys.types.*)
HOST = types.HOST
POINTER = types.POINTER
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
    "DEFAULT_REFRESH_MS",
    "ENCODER",
    "HOST",
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
    "POINTER",
    "QUIT",
    "Device",
    "EncoderDevice",
    "HostEventsDevice",
    "JoystickDevice",
    "JoystickDriver",
    "KeypadDevice",
    "Keys",
    "Runtime",
    "TouchDevice",
    "VirtualDevices",
    "capabilities",
    "chord_matches",
    "default_quit_chord",
    "events",
    "key_triggers_quit",
    "register_device",
    "register_event",
    "types",
]
