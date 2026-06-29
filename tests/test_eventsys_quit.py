# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for eventsys quit helpers and QueueDevice quit chord."""

import unittest

import _env  # noqa: F401
from _support import scripted

import eventsys
from eventsys import Broker, QueueDevice, events, poll_quit_discarding_others
from eventsys.keys import Keys, key_triggers_quit


class TestKeyTriggersQuit(unittest.TestCase):
    def test_keydown_matching_chord(self):
        chord = (Keys.K_q, Keys.KMOD_CTRL)
        self.assertTrue(key_triggers_quit(events.KEYDOWN, Keys.K_q, Keys.KMOD_CTRL, chord))

    def test_keyup_never_triggers(self):
        chord = (Keys.K_q, Keys.KMOD_CTRL)
        self.assertFalse(key_triggers_quit(events.KEYUP, Keys.K_q, Keys.KMOD_CTRL, chord))

    def test_none_chord_disabled(self):
        self.assertFalse(key_triggers_quit(events.KEYDOWN, Keys.K_q, 0, None))


class TestPollQuitDiscardingOthers(unittest.TestCase):
    def test_none_broker_returns_false(self):
        self.assertFalse(poll_quit_discarding_others(None))

    def test_quit_in_batch_returns_true(self):
        broker = Broker()
        q = QueueDevice(
            read=scripted(
                [
                    events.Key(events.KEYDOWN, "A", 65, 0, 0, None),
                    events.Quit(events.QUIT),
                ]
            )
        )
        broker.register(q)
        self.assertTrue(poll_quit_discarding_others(broker))

    def test_non_quit_batch_returns_false(self):
        broker = Broker()
        q = QueueDevice(read=scripted([events.Key(events.KEYDOWN, "A", 65, 0, 0, None)]))
        broker.register(q)
        self.assertFalse(poll_quit_discarding_others(broker))


class TestRegisterQuitCleanup(unittest.TestCase):
    def test_requires_quit_method(self):
        broker = Broker()
        with self.assertRaises(ValueError):
            broker.register_quit_cleanup(object())

    def test_runs_hooks_and_quit(self):
        broker = Broker()
        order = []

        class Resource:
            def quit(self):
                order.append("quit")

        broker.register_quit_cleanup(
            Resource(),
            before=lambda: order.append("before"),
            after=lambda: order.append("after"),
        )
        broker.quit()
        self.assertEqual(order, ["before", "quit", "after"])


class TestQueueDeviceQuitChord(unittest.TestCase):
    def test_chord_keydown_becomes_quit(self):
        class Data:
            quit_chord = (Keys.K_q, Keys.KMOD_CTRL)

        ev = events.Key(events.KEYDOWN, "q", Keys.K_q, Keys.KMOD_CTRL, 0, None)
        dev = QueueDevice(read=scripted([ev]), data=Data())
        out = dev.poll()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, events.QUIT)

    def test_chord_keyup_filtered(self):
        class Data:
            quit_chord = (Keys.K_q, Keys.KMOD_CTRL)

        ev = events.Key(events.KEYUP, "q", Keys.K_q, Keys.KMOD_CTRL, 0, None)
        dev = QueueDevice(read=scripted([ev]), data=Data())
        self.assertEqual(dev.poll(), [])


if __name__ == "__main__":
    unittest.main()
