# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
eventsys — input Runtime and device adapters for *Python.

Quick start::

    import events
    import eventsys

    runtime = eventsys.Runtime()
    keypad = eventsys.KeypadDevice(read=lambda: pressed_keys)
    runtime.register(keypad)

    while True:
        for event in runtime.poll():
            if event.type == events.QUIT:
                break

Optional mappers (import explicitly; not loaded by ``import eventsys``)::

    from eventsys.touch_keypad import TouchKeypad
    from eventsys.joystick_keys import JoystickKeys
"""

from ._capabilities import capabilities
from ._device import Device, register_device, register_device_class, types
from ._encoder import EncoderDevice
from ._host import HostEventsDevice, VirtualDevices
from ._joystick import JoystickDevice, JoystickDriver
from ._keypad import KeypadDevice
from ._runtime import DEFAULT_REFRESH_MS, Runtime
from ._touch import TouchDevice

# Device type constants (also available as eventsys.types.*)
HOST = types.HOST
POINTER = types.POINTER
ENCODER = types.ENCODER
KEYPAD = types.KEYPAD
JOYSTICK = types.JOYSTICK

__all__ = [
    "DEFAULT_REFRESH_MS",
    "ENCODER",
    "HOST",
    "JOYSTICK",
    "KEYPAD",
    "POINTER",
    "Device",
    "EncoderDevice",
    "HostEventsDevice",
    "JoystickDevice",
    "JoystickDriver",
    "KeypadDevice",
    "Runtime",
    "TouchDevice",
    "VirtualDevices",
    "capabilities",
    "register_device",
    "types",
]
