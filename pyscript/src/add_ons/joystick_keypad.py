"""
A class to make a joystick act like a keypad. Taks a mapping from joystick controls to keys.

Example joymap:
{
    1: { # joystick instance_id
        'hats': {
            0: [Keys.K_LEFT, Keys.K_RIGHT, Keys.K_DOWN, Keys.K_UP] # hat index, list of keys to map to
        },
        'buttons': {
            0: Keys.K_RETURN, # button index, key to map to
            1: Keys.K_d,
            2: Keys.K_f,
        }
    }
}

"""

from eventsys import events


class JoystickKeypad:
    def __init__(self, broker, joymap):
        self._broker = broker
        self._joymap = joymap
        self._state = {}
        for j in joymap.values():
            for h in j["hats"].values():
                for key in h:
                    self._state[key] = False
            for b in j["buttons"].values():
                self._state[b] = False
        self._broker.on(
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
        return [k for k, v in self._state.items() if v]
