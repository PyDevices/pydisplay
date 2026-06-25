# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
A class to make keypad keys appear as pins on a microcontroller.

Usage:
    from board_config import display_drv, broker
    from keypins import KeyPins, Keys


    buttons = KeyPins(
        left=Keys.K_LEFT,
        right=Keys.K_RIGHT,
        go=Keys.K_UP,
        stop=Keys.K_DOWN,
        fire=Keys.K_SPACE,
    )

    broker.subscribe(buttons, event_types=[broker.events.KEYDOWN, broker.events.KEYUP])

    while True:
        _ = broker.poll()
        for button in buttons:
            if button.value() == True:
                print(f"{button.name} ({button.keyname}) pressed")
"""

from eventsys import events
from eventsys.keys import Keys


class KeyPins:
    def __init__(self, **kwargs):
        self._keypins = kwargs
        self._objects = {}
        for name, key in kwargs.items():
            setattr(self, name, _KeyPin(name, key))
            self._objects[name] = getattr(self, name)

    def __call__(self, event):
        if event.key in self._keypins.values():
            button = next(name for name, key in self._keypins.items() if key == event.key)
            if event.type == events.KEYDOWN:
                getattr(self, button).value(True)
            elif event.type == events.KEYUP:
                getattr(self, button).value(False)

    def __getitem__(self, name):
        return getattr(self, name)

    def __iter__(self):
        return iter(self._objects.values())

    def __len__(self):
        return len(self._keypins)

    def __repr__(self):
        return repr(self._objects)

    def __str__(self):
        return str(self._keypins)


class _KeyPin:
    def __init__(self, name, key):
        self.name = name
        self.key = key
        self._value = False

    def __call__(self, value=None):
        return self.value(value)

    def value(self, value=None):
        if value is not None:
            self._value = value
            # print(f'setting {self.name} = {self._value}')
        return self._value

    @property
    def keyname(self):
        return Keys.keyname(self.key)
