# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``eventsys`` Runtime and built-in device types."""

import unittest

import _env  # noqa: F401
from _support import FakeDisplay, scripted

import events
import eventsys
from eventsys import (
    Device,
    EncoderDevice,
    HostEventsDevice,
    KeypadDevice,
    Runtime,
    TouchDevice,
    VirtualDevices,
    types,
)
from eventsys._device import _mapping as device_mapping


class TestDeviceBase(unittest.TestCase):
    def test_subscribe_requires_callable(self):
        dev = HostEventsDevice(host_read=scripted(None))
        with self.assertRaises(ValueError):
            dev.subscribe("not callable", [events.KEYDOWN])

    def test_subscribe_rejects_unsupported_event_type(self):
        dev = EncoderDevice()
        with self.assertRaises(ValueError):
            dev.subscribe(lambda e: None, [events.KEYDOWN])

    def test_subscribe_and_unsubscribe_callback(self):
        keys = [{65}, set()]
        dev = KeypadDevice(read=scripted(*keys))
        seen = []
        cb = seen.append
        dev.subscribe(cb, [events.KEYDOWN])
        dev.poll()
        self.assertEqual(len(seen), 1)

        dev.unsubscribe(cb, [events.KEYDOWN])
        keys2 = [{66}]
        dev._read = scripted(*keys2)
        dev.poll()
        self.assertEqual(len(seen), 1)

    def test_user_data_roundtrip(self):
        dev = HostEventsDevice(host_read=scripted(None))
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

        up = dev.poll()
        self.assertEqual(up[0].type, events.KEYUP)
        self.assertEqual(up[0].key, 65)

    def test_no_change_returns_empty_list(self):
        dev = KeypadDevice(read=scripted(set()))
        self.assertEqual(dev.poll(), [])


class TestEncoderDevice(unittest.TestCase):
    def test_turn_emits_wheel(self):
        dev = EncoderDevice(read=scripted(0, 3), read2=scripted(False))
        self.assertEqual(dev.poll(), [])
        wheel = dev.poll()
        self.assertEqual(wheel[0].type, events.MOUSEWHEEL)
        self.assertEqual(wheel[0].y, 3)
        self.assertEqual(wheel[0].x, 0)

    def test_press_emits_button(self):
        dev = EncoderDevice(read=scripted(0), read2=scripted(False, True))
        self.assertEqual(dev.poll(), [])
        btn = dev.poll()
        self.assertEqual(btn[0].type, events.MOUSEBUTTONDOWN)
        self.assertEqual(btn[0].button, 2)


class TestHostEventsDevice(unittest.TestCase):
    def test_forwards_filtered_events(self):
        ev = events.Key(events.KEYDOWN, "A", 65, 0, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]))
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.KEYDOWN)

    def test_empty_read_returns_empty_list(self):
        dev = HostEventsDevice(host_read=scripted(None))
        self.assertEqual(dev.poll(), [])

    def test_touch_scale_on_display(self):
        class ScaledDisplay:
            touch_scale = 2

        ev = events.Button(events.MOUSEBUTTONDOWN, (100, 200), 1, False, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=ScaledDisplay())
        out = dev.poll()
        self.assertEqual(out[0].pos, (50, 100))


class TestVirtualDevicesMultiWindow(unittest.TestCase):
    def test_virtual_device_notifies_multiple_subscribers(self):
        event = events.Key(events.KEYDOWN, "Left Ctrl", 1073742048, 64, 224, 10)
        host = HostEventsDevice(host_read=scripted([event], None))
        keypad = VirtualDevices(host, window_id=10)._vd_keypad
        received = []

        def first(value, *_args):
            received.append(("first", value))

        def second(value, *_args):
            received.append(("second", value))

        keypad.subscribe(first)
        keypad.subscribe(second)
        keypad.poll()

        self.assertEqual(received, [("first", event), ("second", event)])
        keypad.unsubscribe(first)
        keypad.add_event(event)
        keypad.poll()
        self.assertEqual(received[-1], ("second", event))

    def test_fast_key_pairs_preserve_order(self):
        burst = [
            events.Key(events.KEYDOWN, "a", 97, 0, 4, 10),
            events.Key(events.KEYUP, "a", 97, 0, 4, 10),
            events.Key(events.KEYDOWN, "b", 98, 0, 5, 10),
            events.Key(events.KEYUP, "b", 98, 0, 5, 10),
        ]
        host = HostEventsDevice(host_read=scripted(burst, None))
        virtual = VirtualDevices(host, window_id=10)

        virtual.poll_host_device()

        self.assertEqual(virtual._vd_keypad._fifo, burst)
        self.assertTrue(virtual._vd_keypad.has_pending)
        virtual._vd_keypad.poll()
        self.assertTrue(virtual._vd_keypad.has_pending)
        virtual._vd_keypad.poll()
        virtual._vd_keypad.poll()
        virtual._vd_keypad.poll()
        self.assertFalse(virtual._vd_keypad.has_pending)

    def test_overlapping_keys_become_distinct_keypad_presses(self):
        n_down = events.Key(events.KEYDOWN, "n", 110, 0, 17, 10)
        g_down = events.Key(events.KEYDOWN, "g", 103, 0, 10, 10)
        n_up = events.Key(events.KEYUP, "n", 110, 0, 17, 10)
        g_up = events.Key(events.KEYUP, "g", 103, 0, 10, 10)
        host = HostEventsDevice(host_read=scripted([n_down, g_down, n_up, g_up], None))
        virtual = VirtualDevices(host, window_id=10)

        virtual.poll_host_device()

        routed = virtual._vd_keypad._fifo
        self.assertEqual(
            [(e.type, e.key) for e in routed],
            [
                (events.KEYDOWN, 110),
                (events.KEYUP, 110),
                (events.KEYDOWN, 103),
                (events.KEYUP, 103),
            ],
        )

    def test_shared_host_routes_by_window(self):
        host = HostEventsDevice(
            host_read=scripted(
                [
                    events.Button(events.MOUSEBUTTONDOWN, (1, 2), 1, False, 10),
                    events.Button(events.MOUSEBUTTONDOWN, (3, 4), 1, False, 20),
                ]
            )
        )
        a = VirtualDevices(host, window_id=10)
        b = VirtualDevices(host, window_id=20)
        a.poll_host_device()
        self.assertEqual(len(a._vd_pointer._fifo), 1)
        self.assertEqual(a._vd_pointer._fifo[0].pos, (1, 2))
        self.assertEqual(len(b._vd_pointer._fifo), 1)
        self.assertEqual(b._vd_pointer._fifo[0].pos, (3, 4))
        # Non-leader peer must not drain an empty host a second time.
        b.poll_host_device()
        self.assertEqual(len(a._vd_pointer._fifo), 1)


class TestTouchDevice(unittest.TestCase):
    def test_press_move_release_sequence(self):
        disp = FakeDisplay()
        touch = scripted((10, 20), (15, 28), None)
        dev = TouchDevice(read=touch, display=disp)
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
        dev = TouchDevice(read=scripted((5, 7)), display=disp)
        down = dev.poll()
        self.assertEqual(down[0].pos, (7, 234))

    def test_requires_display(self):
        with self.assertRaises(ValueError):
            TouchDevice(read=scripted(None))


class TestRuntime(unittest.TestCase):
    def test_on_rejects_non_callable(self):
        runtime = Runtime()
        with self.assertRaises(ValueError):
            runtime.on(events.KEYDOWN, "nope")

    def test_poll_aggregates_registered_devices(self):
        runtime = Runtime()
        kp = KeypadDevice(read=scripted({65}, set()))
        runtime.register(kp)
        self.assertIs(kp.runtime, runtime)

        out = runtime.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.KEYDOWN)

    def test_poll_empty_is_list(self):
        runtime = Runtime()
        self.assertEqual(runtime.poll(), [])

    def test_device_type_subscription(self):
        runtime = Runtime()
        kp = KeypadDevice(read=scripted({66}, set()))
        runtime.register(kp)
        seen = []
        runtime.on_device(types.KEYPAD, seen.append)
        runtime.poll()
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].key, 66)

    def test_unregister(self):
        runtime = Runtime()
        dev = HostEventsDevice(host_read=scripted(None))
        runtime.register(dev)
        runtime.unregister(dev)
        self.assertNotIn(dev, runtime.devices)
        self.assertIsNone(dev.runtime)

    def test_before_quit_must_be_callable(self):
        runtime = Runtime()
        with self.assertRaises(ValueError):
            runtime.before_quit = 5

    def test_touch_read_must_be_callable(self):
        with self.assertRaises(TypeError):
            Runtime(displays=[FakeDisplay()], touch_read=(lambda: None,))

    def test_add_keypad(self):
        runtime = Runtime()
        dev = runtime.add_keypad(read=scripted(set()))
        self.assertIs(runtime.keypad_dev, dev)
        self.assertIn(dev, runtime.devices)

    def test_requires_async_timer_rejects_sync(self):
        display = FakeDisplay()
        display.requires_async_timer = True
        display.needs_refresh = False
        with self.assertRaises(RuntimeError) as ctx:
            Runtime(displays=[display], timer_async=False)
        self.assertIn("requires timer_async=True", str(ctx.exception))

    def test_requires_async_timer_allows_async(self):
        display = FakeDisplay()
        display.requires_async_timer = True
        display.needs_refresh = False
        runtime = Runtime(displays=[display], timer_async=True)
        self.addCleanup(runtime.stop_timer)
        self.assertTrue(runtime.timer_async)


class TestRegisterDevice(unittest.TestCase):
    def setUp(self):
        self._names = []

    def tearDown(self):
        for name, value in self._names:
            if hasattr(types, name):
                delattr(types, name)
            device_mapping.pop(value, None)

    def test_create_custom_device_type(self):
        cls = eventsys.register_device("MYPAD", [events.KEYDOWN, events.KEYUP])
        self._names.append(("MYPAD", cls.type))
        self.assertTrue(issubclass(cls, Device))
        self.assertEqual(cls.__name__, "MypadDevice")
        self.assertEqual(cls.responses, [events.KEYDOWN, events.KEYUP])
        self.assertEqual(types.MYPAD, cls.type)

    def test_invalid_arguments_raise(self):
        with self.assertRaises(ValueError):
            eventsys.register_device(123, [])
        with self.assertRaises(ValueError):
            eventsys.register_device("OK", "not a list")
        with self.assertRaises(ValueError):
            eventsys.register_device("OK", ["not an int"])


if __name__ == "__main__":
    unittest.main()
