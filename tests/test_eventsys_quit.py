# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for eventsys quit helpers and HostEventsDevice quit chord."""

import unittest

import _env  # noqa: F401
from _support import scripted

import eventsys
from eventsys import HostEventsDevice, Runtime, events
from eventsys.keys import Keys, default_quit_chord, key_triggers_quit


class TestDefaultQuitChord(unittest.TestCase):
    def test_default_quit_chord_is_ctrl_q(self):
        self.assertEqual(default_quit_chord(), (Keys.K_q, Keys.KMOD_CTRL))

    def test_exported_from_eventsys(self):
        self.assertEqual(eventsys.default_quit_chord(), (Keys.K_q, Keys.KMOD_CTRL))


class TestKeyTriggersQuit(unittest.TestCase):
    def test_keydown_matching_chord(self):
        chord = default_quit_chord()
        self.assertTrue(key_triggers_quit(events.KEYDOWN, Keys.K_q, Keys.KMOD_CTRL, chord))

    def test_keyup_never_triggers(self):
        chord = default_quit_chord()
        self.assertFalse(key_triggers_quit(events.KEYUP, Keys.K_q, Keys.KMOD_CTRL, chord))

    def test_none_chord_disabled(self):
        self.assertFalse(key_triggers_quit(events.KEYDOWN, Keys.K_q, 0, None))


class TestQuitRequested(unittest.TestCase):
    def test_none_runtime_poll_is_noop(self):
        runtime = Runtime()
        self.assertFalse(runtime.quit_requested)

    def test_quit_sets_flag(self):
        class Display:
            needs_refresh = False

            def quit(self):
                pass

        runtime = Runtime(display=Display())
        host = HostEventsDevice(
            host_read=scripted([events.Quit(events.QUIT)]),
            display=Display(),
        )
        runtime.register(host)
        runtime.poll()
        self.assertTrue(runtime.quit_requested)


class TestRuntimeQuitLifecycle(unittest.TestCase):
    def test_before_quit_then_display_quit(self):
        order = []

        class Display:
            needs_refresh = False

            def quit(self):
                order.append("quit")

        runtime = Runtime(display=Display())
        runtime.before_quit = lambda: order.append("before")
        runtime._handle_quit()
        self.assertEqual(order, ["before", "quit"])
        self.assertTrue(runtime.quit_requested)


class TestHostEventsDeviceQuitChord(unittest.TestCase):
    def test_chord_keydown_becomes_quit(self):
        class Data:
            quit_chord = default_quit_chord()

        ev = events.Key(events.KEYDOWN, "q", Keys.K_q, Keys.KMOD_CTRL, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.QUIT)

    def test_chord_keyup_filtered(self):
        class Data:
            quit_chord = default_quit_chord()

        ev = events.Key(events.KEYUP, "q", Keys.K_q, Keys.KMOD_CTRL, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        self.assertEqual(dev.poll(), [])

    def test_ac_back_keydown_becomes_quit(self):
        """Android system Back (SDLK_AC_BACK) maps to QUIT without a chord."""

        class Data:
            quit_chord = default_quit_chord()

        ev = events.Key(events.KEYDOWN, "AC Back", Keys.K_AC_BACK, 0, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.QUIT)

    def test_ac_back_works_without_quit_chord(self):
        class Data:
            pass

        ev = events.Key(events.KEYDOWN, "AC Back", Keys.K_AC_BACK, 0, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.QUIT)

    def test_ac_back_keyup_filtered(self):
        class Data:
            pass

        ev = events.Key(events.KEYUP, "AC Back", Keys.K_AC_BACK, 0, 0, None)
        dev = HostEventsDevice(host_read=scripted([ev]), display=Data())
        self.assertEqual(dev.poll(), [])


class TestKeyTriggersQuitAcBack(unittest.TestCase):
    def test_ac_back_triggers(self):
        self.assertTrue(key_triggers_quit(events.KEYDOWN, Keys.K_AC_BACK, 0, None))

    def test_ac_back_keyup_does_not(self):
        self.assertFalse(key_triggers_quit(events.KEYUP, Keys.K_AC_BACK, 0, None))


if __name__ == "__main__":
    unittest.main()
