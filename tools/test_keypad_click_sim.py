"""Simulate Keypad level-read behavior for quick clicks (no SDL)."""

import sys

sys.path[:0] = ["src/lib", "src/add_ons"]

from touch_keypad import Keypad  # noqa: E402

from eventsys import events  # noqa: E402


class MockBroker:
    def __init__(self):
        self._subs = {}

    def subscribe(self, cb, event_types=None):
        for et in event_types or []:
            self._subs.setdefault(et, set()).add(cb)

    def inject(self, event):
        for cb in self._subs.get(event.type, ()):
            cb(event)


def evt(etype, pos):
    class E:
        pass

    e = E()
    e.type = etype
    e.button = 1
    e.pos = pos
    return e


broker = MockBroker()
keypad = Keypad(broker, 2, 233, 7 * 45, 3 * 45, cols=7, rows=3)
pos = (50, 250)

broker.inject(evt(events.MOUSEBUTTONDOWN, pos))
broker.inject(evt(events.MOUSEBUTTONUP, pos))
after_quick_click_held = keypad.read_held()
after_quick_click_edge = keypad.read()

broker.inject(evt(events.MOUSEBUTTONDOWN, pos))
after_down_only = keypad.read_held()

print(f"quick_click_held_read={after_quick_click_held!r}")
print(f"quick_click_edge_read={after_quick_click_edge!r}")
print(f"down_only_read={after_down_only!r}")
