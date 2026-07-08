# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``eventsys.JoystickDevice``."""

import unittest

import _env  # noqa: F401

from eventsys import JoystickDevice, Runtime, events, types


class _MockJoystick:
    def __init__(self):
        self._axes = [0.0, 0.0]
        self._buttons = [False, False]
        self._hats = [(0, 0)]

    def get_instance_id(self):
        return 1

    def get_numaxes(self):
        return len(self._axes)

    def get_axis(self, axis):
        return self._axes[axis]

    def get_numbuttons(self):
        return len(self._buttons)

    def get_button(self, button):
        return self._buttons[button]

    def get_numhats(self):
        return len(self._hats)

    def get_hat(self, hat):
        return self._hats[hat]

    def get_numballs(self):
        return 0

    def get_ball(self, ball):
        return (0, 0)


class TestJoystickDevice(unittest.TestCase):
    def test_axis_motion(self):
        driver = _MockJoystick()
        dev = JoystickDevice(joystick_driver=driver)
        self.assertEqual(dev.poll(), [])
        driver._axes[0] = 0.5
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.JOYAXISMOTION)
        self.assertEqual(out[0].axis, 0)
        self.assertEqual(out[0].value, 0.5)

    def test_button_down_up(self):
        driver = _MockJoystick()
        dev = JoystickDevice(joystick_driver=driver)
        driver._buttons[1] = True
        down = dev.poll()
        self.assertEqual(down[0].type, events.JOYBUTTONDOWN)
        driver._buttons[1] = False
        up = dev.poll()
        self.assertEqual(up[0].type, events.JOYBUTTONUP)

    def test_emulate_digital_hat(self):
        driver = _MockJoystick()
        dev = JoystickDevice(joystick_driver=driver, emulate_digital=[(0, 1)])
        driver._axes[0] = 0.9
        out = dev.poll()
        types_out = [e.type for e in out]
        self.assertIn(events.JOYAXISMOTION, types_out)
        self.assertIn(events.JOYHATMOTION, types_out)

    def test_runtime_on_device_dispatch(self):
        driver = _MockJoystick()
        runtime = Runtime()
        dev = JoystickDevice(joystick_driver=driver)
        runtime.register(dev)
        seen = []
        runtime.on_device(types.JOYSTICK, seen.append)
        driver._buttons[0] = True
        runtime.poll()
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].type, events.JOYBUTTONDOWN)


if __name__ == "__main__":
    unittest.main()
