# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for HostEventsDevice quit_chord handling."""

import unittest

import _env  # noqa: F401
from _support import scripted

import events
from eventsys import HostEventsDevice, Runtime
import keys

_CTRL_Q = (keys.K_q, keys.KMOD_CTRL)
_AC_BACK = (keys.K_AC_BACK, 0)


class TestQuitRequested(unittest.TestCase):
    def test_none_runtime_poll_is_noop(self):
        runtime = Runtime()
        self.assertFalse(runtime.quit_requested)


class TestRuntimeQuitLifecycle(unittest.TestCase):
    def test_before_quit_then_display_quit(self):
        order = []

        class Display:
            needs_refresh = False

            def quit(self):
                order.append("quit")

        runtime = Runtime(displays=[Display()])
        runtime.before_quit = lambda: order.append("before")
        runtime._handle_quit()
        self.assertTrue(runtime.quit_requested)
        # Quit always defers teardown (avoid re-entrant GUI deinit); flush it.
        runtime._try_perform_teardown()
        self.assertEqual(order, ["before", "quit"])


class TestHostEventsDeviceQuitChord(unittest.TestCase):
    def test_chord_keydown_becomes_quit(self):
        class Data:
            quit_chord = _CTRL_Q

        ev = events.Key(events.KEYDOWN, "q", keys.K_q, keys.KMOD_CTRL, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.QUIT)

    def test_chord_keyup_filtered(self):
        class Data:
            quit_chord = _CTRL_Q

        ev = events.Key(events.KEYUP, "q", keys.K_q, keys.KMOD_CTRL, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        self.assertEqual(dev.poll(), [])

    def test_ac_back_keydown_becomes_quit(self):
        class Data:
            quit_chord = _AC_BACK

        ev = events.Key(events.KEYDOWN, "AC Back", keys.K_AC_BACK, 0, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.QUIT)

    def test_ac_back_ignored_without_quit_chord(self):
        class Data:
            pass

        ev = events.Key(events.KEYDOWN, "AC Back", keys.K_AC_BACK, 0, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.KEYDOWN)

    def test_ac_back_keyup_filtered(self):
        class Data:
            quit_chord = _AC_BACK

        ev = events.Key(events.KEYUP, "AC Back", keys.K_AC_BACK, 0, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        self.assertEqual(dev.poll(), [])

    def test_none_quit_chord_does_not_match(self):
        class Data:
            quit_chord = None

        ev = events.Key(events.KEYDOWN, "q", keys.K_q, keys.KMOD_CTRL, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.KEYDOWN)


class TestChordMatches(unittest.TestCase):
    def test_ctrl_q(self):
        self.assertTrue(keys.chord_matches(_CTRL_Q, keys.K_q, keys.KMOD_CTRL))
        self.assertTrue(keys.chord_matches(_CTRL_Q, keys.K_q, keys.KMOD_RCTRL))
        self.assertFalse(keys.chord_matches(_CTRL_Q, keys.K_q, 0))

    def test_ac_back_no_mod(self):
        self.assertTrue(keys.chord_matches(_AC_BACK, keys.K_AC_BACK, 0))
        self.assertTrue(keys.chord_matches(_AC_BACK, keys.K_AC_BACK, keys.KMOD_CTRL))
        self.assertFalse(keys.chord_matches(_AC_BACK, keys.K_q, 0))


if __name__ == "__main__":
    unittest.main()
