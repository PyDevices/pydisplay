from machine import ADC, Pin

from eventsys.joystick import JoystickDriver


class GPIOJoystick(JoystickDriver):
    """
    A driver for a joystick that uses GPIO inputs.

    Args:
        instance_id: The instance ID of the joystick. (pygame joystick index)
        axes: A list of ADC objects for the axes.
        buttons: A list of Pin objects for the buttons.
        button_high: True if logic high when button is pressed.
        hats: A list of tuples of Pin objects for the hats. A hat is a 4-way switch, like a d-pad. 4 pins: left, right, down, up.
    """

    def __init__(
        self,
        instance_id: int,
        axes: list[ADC],
        buttons=None,
        button_high: bool = False,
        hats=None,
    ):
        if hats is None:
            hats = []
        if buttons is None:
            buttons = []
        self._instance_id = instance_id
        self._axes = axes
        self._buttons = buttons
        self._hats = hats
        self._button_high = button_high

    def get_instance_id(self):
        return self._instance_id

    def get_numaxes(self):
        return len(self._axes)

    def get_numbuttons(self):
        return len(self._buttons)

    def get_numhats(self):
        return len(self._hats)

    def get_axis(self, axis):
        return self._axes[axis].read_u16() / 32767.5 - 1

    def get_button(self, button):
        cmp = 1 if self._button_high else 0
        return self._buttons[button].value() == cmp

    def get_hat(self, hat):
        l, r, d, u = self._hats[hat]
        cmp = 1 if self._button_high else 0
        if (l.value() == cmp and r.value() == cmp) or (u.value() == cmp and d.value() == cmp):
            raise ValueError("Hat is in an invalid position")

        return (
            -1 if l.value() == cmp else 1 if r.value() == cmp else 0,
            -1 if d.value() == cmp else 1 if u.value() == cmp else 0,
        )

    def get_numballs(self):
        return 0
