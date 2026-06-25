# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the ``eventsys`` event types/classes and ``custom_type``."""

import unittest

import _env  # noqa: F401

import eventsys
from eventsys import events


class TestEventTypes(unittest.TestCase):
    def test_type_constants_are_ints(self):
        for name in ("QUIT", "KEYDOWN", "KEYUP", "MOUSEMOTION", "MOUSEBUTTONDOWN"):
            self.assertIsInstance(getattr(events, name), int)

    def test_filter_contains_known_types(self):
        self.assertIn(events.KEYDOWN, events.filter)
        self.assertIn(events.MOUSEWHEEL, events.filter)
        self.assertIn(events.QUIT, events.filter)

    def test_namedtuple_fields(self):
        self.assertEqual(events.Key._fields, ("type", "name", "key", "mod", "scancode", "window"))
        self.assertEqual(
            events.Motion._fields, ("type", "pos", "rel", "buttons", "touch", "window")
        )
        self.assertEqual(events.Button._fields, ("type", "pos", "button", "touch", "window"))

    def test_key_namedtuple_roundtrip(self):
        ev = events.Key(events.KEYDOWN, "A", 65, 0, 0, None)
        self.assertEqual(ev.type, events.KEYDOWN)
        self.assertEqual(ev.name, "A")
        self.assertEqual(ev.key, 65)


class TestCustomType(unittest.TestCase):
    def setUp(self):
        self._added_types = []
        self._added_classes = []

    def tearDown(self):
        # custom_type() mutates the shared ``events`` class; undo it so the
        # tests stay independent and idempotent within a single process.
        for name in self._added_types + self._added_classes:
            if hasattr(events, name):
                delattr(events, name)

    def _add_type(self, name, value):
        self._added_types.append(name)
        return name, value

    def _add_class(self, name):
        self._added_classes.append(name)
        return name

    def test_create_type_and_class(self):
        tname, tval = self._add_type("MYEVT", 0x9100)
        cname = self._add_class("Myevt")
        eventsys.custom_type(types={tname: tval}, classes={cname: "type a b"})

        self.assertEqual(events.MYEVT, 0x9100)
        instance = events.Myevt(events.MYEVT, 1, 2)
        self.assertEqual(instance.type, events.MYEVT)
        self.assertEqual(instance.a, 1)
        self.assertEqual(instance.b, 2)

    def test_auto_allocated_value_uses_user_base(self):
        base = events._USER_TYPE_BASE
        tname, _ = self._add_type("MYAUTO", 0)  # value 0/None -> auto allocate
        eventsys.custom_type(types={tname: 0})
        self.assertEqual(events.MYAUTO, base)
        self.assertEqual(events._USER_TYPE_BASE, base + 1)

    def test_duplicate_type_raises(self):
        tname, tval = self._add_type("MYDUP", 0x9200)
        eventsys.custom_type(types={tname: tval})
        with self.assertRaises(ValueError):
            eventsys.custom_type(types={tname: tval})

    def test_duplicate_class_raises(self):
        cname = self._add_class("Mydupcls")
        eventsys.custom_type(classes={cname: "type a"})
        with self.assertRaises(ValueError):
            eventsys.custom_type(classes={cname: "type a"})


if __name__ == "__main__":
    unittest.main()
