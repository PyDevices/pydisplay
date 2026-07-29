# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Optional eventsys mapper: joystick hat/buttons → held key-code state.

``JoystickKeys`` is **not** a :class:`~eventsys.JoystickDevice` and not a keypad.
It does not poll hardware, enqueue events, or synthesize ``KEYDOWN`` /
``KEYUP``.  It subscribes to a :class:`~eventsys.Runtime` and updates an internal
held-key map from ``JOYHATMOTION`` / ``JOYBUTTON*`` using a ``joymap``.

Import explicitly (not loaded by ``import eventsys``)::

    from eventsys.joystick_keys import JoystickKeys
    from eventsys import Keys

    joymap = {
        1: {  # joystick instance_id
            "hats": {
                # hat index → [left, right, down, up] key codes
                0: [Keys.K_LEFT, Keys.K_RIGHT, Keys.K_DOWN, Keys.K_UP],
            },
            "buttons": {
                0: Keys.K_RETURN,
                1: Keys.K_d,
                2: Keys.K_f,
            },
        }
    }
    joy = JoystickKeys(runtime, joymap)
    while True:
        runtime.poll()
        if held := joy.read():
            print(held)
"""

from ._events import events


class JoystickKeys:
    """Map joystick hat directions and buttons onto held key codes.

    Subscribes to ``JOYHATMOTION``, ``JOYBUTTONDOWN``, and ``JOYBUTTONUP``.
    ``read()`` returns the list of key codes currently held according to
    ``joymap`` (per joystick ``instance_id``).
    """

    def __init__(self, runtime, joymap):
        self._runtime = runtime
        self._joymap = joymap
        self._state = {}
        for j in joymap.values():
            for h in j["hats"].values():
                for key in h:
                    self._state[key] = False
            for b in j["buttons"].values():
                self._state[b] = False
        self._runtime.on(
            [events.JOYHATMOTION, events.JOYBUTTONDOWN, events.JOYBUTTONUP],
            self.callback,
        )

    def callback(self, event):
        if (
            event.type == events.JOYHATMOTION
            and (j := self._joymap.get(event.instance_id))
            and (h := j["hats"].get(event.hat))
        ):
            x, y = event.value
            self._state[h[0]] = x == -1
            self._state[h[1]] = x == 1
            self._state[h[2]] = y == -1
            self._state[h[3]] = y == 1
            return
        if (
            event.type in [events.JOYBUTTONDOWN, events.JOYBUTTONUP]
            and (j := self._joymap.get(event.instance_id))
            and (b := j["buttons"].get(event.button))
        ):
            self._state[b] = event.type == events.JOYBUTTONDOWN
            return

    def read(self):
        """Return key codes currently held according to ``joymap``."""
        return [k for k, v in self._state.items() if v]
