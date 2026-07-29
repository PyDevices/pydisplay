# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Joystick device and driver interface."""

from ._device import Device, register_device_class, types
from ._events import events


class JoystickDriver:
    """PyGame/SDL-style joystick polling interface."""

    def get_instance_id(self):
        """Return the SDL/PyGame instance id for this joystick."""
        raise NotImplementedError("JoystickDriver.get_instance_id() not implemented")

    def get_numaxes(self):
        """Return the number of axes."""
        raise NotImplementedError("JoystickDriver.get_numaxes() not implemented")

    def get_axis(self, axis):
        """Return the axis value in ``[-1.0, 1.0]``.

        Args:
            axis: Zero-based axis index.
        """
        raise NotImplementedError("JoystickDriver.get_axis() not implemented")

    def get_numballs(self):
        """Return the number of trackballs."""
        raise NotImplementedError("JoystickDriver.get_numballs() not implemented")

    def get_ball(self, ball):
        """Return ``(dx, dy)`` relative motion for a trackball.

        Args:
            ball: Zero-based trackball index.
        """
        raise NotImplementedError("JoystickDriver.get_ball() not implemented")

    def get_numbuttons(self):
        """Return the number of buttons."""
        raise NotImplementedError("JoystickDriver.get_numbuttons() not implemented")

    def get_button(self, button):
        """Return whether a button is pressed.

        Args:
            button: Zero-based button index.
        """
        raise NotImplementedError("JoystickDriver.get_button() not implemented")

    def get_numhats(self):
        """Return the number of hats (D-pads)."""
        raise NotImplementedError("JoystickDriver.get_numhats() not implemented")

    def get_hat(self, hat):
        """Return ``(x, y)`` hat position with each component in ``{-1, 0, 1}``.

        Args:
            hat: Zero-based hat index.
        """
        raise NotImplementedError("JoystickDriver.get_hat() not implemented")


class JoystickDevice(Device):
    """Joystick mapped to SDL joystick events."""

    type = types.JOYSTICK
    responses = (
        events.JOYAXISMOTION,
        events.JOYBALLMOTION,
        events.JOYHATMOTION,
        events.JOYBUTTONDOWN,
        events.JOYBUTTONUP,
    )

    def __init__(
        self,
        *args,
        joystick_driver: JoystickDriver,
        emulate_digital=None,
        digital_threshold: float = 0.5,
        **kwargs,
    ):
        """Create a joystick device backed by ``joystick_driver``.

        Args:
            *args: Forwarded to :class:`Device`.
            joystick_driver: Object implementing :class:`JoystickDriver`.
            emulate_digital: Optional sequence of ``(axis_x, axis_y)`` pairs to
                synthesize extra hat events from analog axes.
            digital_threshold: Absolute axis magnitude for :meth:`emulate`.
            **kwargs: Forwarded to :class:`Device`.
        """
        super().__init__(*args, **kwargs)
        self.joystick_driver = joystick_driver
        self.emulate_digital = emulate_digital
        self.digital_threshold = digital_threshold
        self._state = [
            [0] * self.joystick_driver.get_numaxes(),
            [False] * self.joystick_driver.get_numbuttons(),
            [(0, 0)] * self.joystick_driver.get_numhats(),
            [(0, 0)] * self.joystick_driver.get_numballs(),
        ]
        if self.emulate_digital:
            self._state.append([0] * len(self.emulate_digital))

    def emulate(self, value):
        """Map an analog axis value to ``-1``, ``0``, or ``1`` by threshold.

        Args:
            value: Axis sample in approximately ``[-1.0, 1.0]``.

        Returns:
            int: Digitized hat component.
        """
        return (
            -1 if value < -self.digital_threshold else 1 if value > self.digital_threshold else 0
        )

    def _poll(self):
        eventlist = []
        new_state = [
            [self.joystick_driver.get_axis(i) for i in range(self.joystick_driver.get_numaxes())],
            [
                self.joystick_driver.get_button(i)
                for i in range(self.joystick_driver.get_numbuttons())
            ],
            [self.joystick_driver.get_hat(i) for i in range(self.joystick_driver.get_numhats())],
            [self.joystick_driver.get_ball(i) for i in range(self.joystick_driver.get_numballs())],
        ]

        instance_id = self.joystick_driver.get_instance_id()

        for i, (old, new) in enumerate(zip(self._state[0], new_state[0])):
            if old != new:
                eventlist.append(events.JoyAxisMotion(events.JOYAXISMOTION, instance_id, i, new))

        for i, (old, new) in enumerate(zip(self._state[1], new_state[1])):
            if old != new:
                eventlist.append(
                    events.JoyButtonDown(events.JOYBUTTONDOWN, instance_id, i)
                    if new
                    else events.JoyButtonUp(events.JOYBUTTONUP, instance_id, i)
                )

        for i, (old, new) in enumerate(zip(self._state[2], new_state[2])):
            if old != new:
                eventlist.append(events.JoyHatMotion(events.JOYHATMOTION, instance_id, i, new))

        for i, (old, new) in enumerate(zip(self._state[3], new_state[3])):
            if old != new:
                eventlist.append(events.JoyBallMotion(events.JOYBALLMOTION, instance_id, i, new))

        if self.emulate_digital:
            axes = new_state[0]
            new_state.append(
                [(self.emulate(axes[x]), self.emulate(axes[y])) for x, y in self.emulate_digital]
            )
            for i, (old, new) in enumerate(zip(self._state[4], new_state[4])):
                if old != new:
                    eventlist.append(
                        events.JoyHatMotion(
                            events.JOYHATMOTION,
                            instance_id,
                            i + self.joystick_driver.get_numhats(),
                            new,
                        )
                    )

        self._state = new_state
        return eventlist if eventlist else None


register_device_class(types.JOYSTICK, JoystickDevice)
