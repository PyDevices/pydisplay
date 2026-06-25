# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``eventsys.devices`` (Broker and the concrete device types)."""

import unittest

import _env  # noqa: F401
from _support import FakeDisplay, scripted

from eventsys import devices, events
from eventsys.devices import (
    Broker,
    Device,
    EncoderDevice,
    KeypadDevice,
    QueueDevice,
    TouchDevice,
    types,
)


class TestDeviceBase(unittest.TestCase):
    def test_subscribe_requires_callable(self):
        dev = QueueDevice(read=scripted(None))
        with self.assertRaises(ValueError):
            dev.subscribe("not callable", [events.KEYDOWN])

    def test_subscribe_rejects_unsupported_event_type(self):
        dev = EncoderDevice()  # responds to wheel + buttons, not KEYDOWN
        with self.assertRaises(ValueError):
            dev.subscribe(lambda e: None, [events.KEYDOWN])

    def test_subscribe_and_unsubscribe_callback(self):
        keys = [{65}, set()]
        dev = KeypadDevice(read=scripted(*keys))
        seen = []
        cb = seen.append
        dev.subscribe(cb, [events.KEYDOWN])
        dev.poll()  # KEYDOWN -> callback fires
        self.assertEqual(len(seen), 1)

        dev.unsubscribe(cb, [events.KEYDOWN])
        keys2 = [{66}]
        dev._read = scripted(*keys2)
        dev.poll()
        self.assertEqual(len(seen), 1)  # no further callbacks

    def test_user_data_roundtrip(self):
        dev = QueueDevice(read=scripted(None))
        dev.user_data = {"hello": 1}
        self.assertEqual(dev.user_data, {"hello": 1})


class TestKeypadDevice(unittest.TestCase):
    def test_keydown_then_keyup(self):
        dev = KeypadDevice(read=scripted({65}, set()))
        down = dev.poll()
        self.assertEqual(len(down), 1)
        self.assertEqual(down[0].type, events.KEYDOWN)
        self.assertEqual(down[0].key, 65)
        self.assertEqual(down[0].name, "A")
        self.assertEqual(down[0].window, None)

        up = dev.poll()
        self.assertEqual(up[0].type, events.KEYUP)
        self.assertEqual(up[0].key, 65)

    def test_no_change_returns_none(self):
        dev = KeypadDevice(read=scripted(set()))
        self.assertIsNone(dev.poll())


class TestEncoderDevice(unittest.TestCase):
    def test_turn_emits_wheel(self):
        dev = EncoderDevice(read=scripted(0, 3), read2=scripted(False))
        self.assertIsNone(dev.poll())  # first poll establishes baseline
        wheel = dev.poll()
        self.assertEqual(wheel[0].type, events.MOUSEWHEEL)
        # default button 2 (even) -> vertical movement
        self.assertEqual(wheel[0].y, 3)
        self.assertEqual(wheel[0].x, 0)

    def test_press_emits_button(self):
        dev = EncoderDevice(read=scripted(0), read2=scripted(False, True))
        self.assertIsNone(dev.poll())
        btn = dev.poll()
        self.assertEqual(btn[0].type, events.MOUSEBUTTONDOWN)
        self.assertEqual(btn[0].button, 2)


class TestQueueDevice(unittest.TestCase):
    def test_forwards_filtered_events(self):
        ev = events.Key(events.KEYDOWN, "A", 65, 0, 0, None)
        dev = QueueDevice(read=scripted([ev]))
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.KEYDOWN)

    def test_empty_read_returns_none(self):
        dev = QueueDevice(read=scripted(None))
        self.assertIsNone(dev.poll())

    def test_touch_scale_on_display_data(self):
        class ScaledDisplay:
            touch_scale = 2

        ev = events.Button(events.MOUSEBUTTONDOWN, (100, 200), 1, False, None)
        dev = QueueDevice(read=scripted([ev]), data=ScaledDisplay())
        out = dev.poll()
        self.assertEqual(out[0].pos, (50, 100))


class TestTouchDevice(unittest.TestCase):
    def test_press_move_release_sequence(self):
        disp = FakeDisplay()
        touch = scripted((10, 20), (15, 28), None)
        dev = TouchDevice(read=touch, data=disp)
        self.assertIs(disp.touch_device, dev)

        down = dev.poll()
        self.assertEqual(down[0].type, events.MOUSEBUTTONDOWN)
        self.assertEqual(down[0].pos, (10, 20))

        move = dev.poll()
        self.assertEqual(move[0].type, events.MOUSEMOTION)
        self.assertEqual(move[0].pos, (15, 28))
        self.assertEqual(move[0].rel, (5, 8))

        up = dev.poll()
        self.assertEqual(up[0].type, events.MOUSEBUTTONUP)

    def test_rotation_transforms_coordinates(self):
        disp = FakeDisplay(width=320, height=240, rotation=90)
        dev = TouchDevice(read=scripted((5, 7)), data=disp)
        # 90 deg -> swap_xy + reverse_y: (5, 7) -> swap (7, 5) -> y = 240-5-1
        down = dev.poll()
        self.assertEqual(down[0].pos, (7, 234))

    def test_requires_data(self):
        with self.assertRaises(ValueError):
            TouchDevice(read=scripted(None))


class TestBroker(unittest.TestCase):
    def test_subscribe_requires_exactly_one_of_event_or_device_types(self):
        broker = Broker()
        with self.assertRaises(ValueError):
            broker.subscribe(lambda e: None)
        with self.assertRaises(ValueError):
            broker.subscribe(
                lambda e: None, event_types=[events.KEYDOWN], device_types=[types.KEYPAD]
            )

    def test_poll_aggregates_registered_devices(self):
        broker = Broker()
        kp = KeypadDevice(read=scripted({65}, set()))
        broker.register_device(kp)
        self.assertIs(kp.broker, broker)

        out = broker.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.KEYDOWN)

    def test_device_type_subscription(self):
        broker = Broker()
        kp = KeypadDevice(read=scripted({66}, set()))
        broker.register_device(kp)
        seen = []
        broker.subscribe(seen.append, device_types=[types.KEYPAD])
        broker.poll()
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].key, 66)

    def test_create_device_registers_it(self):
        broker = Broker()
        dev = broker.create_device(types.QUEUE, read=scripted(None))
        self.assertIn(dev, broker.devices)
        self.assertIsInstance(dev, QueueDevice)

    def test_create_device_invalid_type_raises(self):
        broker = Broker()
        with self.assertRaises(ValueError):
            broker.create_device(0x999)

    def test_unregister_device(self):
        broker = Broker()
        dev = broker.create_device(types.QUEUE, read=scripted(None))
        broker.unregister_device(dev)
        self.assertNotIn(dev, broker.devices)
        self.assertIsNone(dev.broker)

    def test_quit_func_must_be_callable(self):
        broker = Broker()
        with self.assertRaises(ValueError):
            broker.quit_func = 5

    def test_quit_calls_custom_quit_func(self):
        broker = Broker()
        called = []
        broker.quit_func = lambda: called.append(True)
        broker.quit()
        self.assertTrue(called)


class TestDevicesCustomType(unittest.TestCase):
    def setUp(self):
        self._names = []

    def tearDown(self):
        # devices.custom_type() mutates the module-level ``types`` class and the
        # ``_mapping`` registry; undo both so tests stay independent.
        for name, value in self._names:
            if hasattr(types, name):
                delattr(types, name)
            devices._mapping.pop(value, None)

    def test_create_custom_device_type(self):
        cls = devices.custom_type("MYPAD", [events.KEYDOWN, events.KEYUP])
        self._names.append(("MYPAD", cls.type))
        self.assertTrue(issubclass(cls, Device))
        self.assertEqual(cls.__name__, "MypadDevice")
        self.assertEqual(cls.responses, [events.KEYDOWN, events.KEYUP])
        self.assertEqual(types.MYPAD, cls.type)

    def test_invalid_arguments_raise(self):
        with self.assertRaises(ValueError):
            devices.custom_type(123, [])
        with self.assertRaises(ValueError):
            devices.custom_type("OK", "not a list")
        with self.assertRaises(ValueError):
            devices.custom_type("OK", ["not an int"])


if __name__ == "__main__":
    unittest.main()
